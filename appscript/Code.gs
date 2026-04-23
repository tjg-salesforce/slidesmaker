var TEMPLATE_ID = '1kfgV1fhspnWUE0I4uCcSi5a764X-jQamOzVZTygyad4';
var ICON_LIBRARY_ID = '1i_aLUcHQwnPjEAFIlK6x4jmuKZ2PD1J5eDYxyNEyIew';

function doGet() {
  return HtmlService.createHtmlOutputFromFile('Form')
    .setTitle('QBR Deck Generator')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function generateFromForm(jsonString, userEmail, title) {
  var replacements = JSON.parse(jsonString);
  var deckUrl = buildDeck(TEMPLATE_ID, title || 'QBR Deck', replacements, userEmail);
  return deckUrl;
}

function doPost(e) {
  try {
    var payload = JSON.parse(e.postData.contents);
    var title = payload.title || 'QBR Deck';
    var userEmail = payload.user_email;
    var replacements = payload.replacements || {};
    var templateId = payload.template_id || TEMPLATE_ID;

    if (!userEmail) {
      return _jsonResponse({ error: 'missing user_email' }, 400);
    }

    var deckUrl = buildDeck(templateId, title, replacements, userEmail);
    return _jsonResponse({ deck_url: deckUrl });

  } catch (err) {
    Logger.log('doPost error: ' + err.message + '\n' + err.stack);
    return _jsonResponse({ error: err.message }, 500);
  }
}

function buildDeck(templateId, title, replacements, userEmail) {
  var copy = DriveApp.getFileById(templateId).makeCopy(title);
  var presentationId = copy.getId();

  var presentation = SlidesApp.openById(presentationId);
  var slides = presentation.getSlides();

  for (var i = 0; i < slides.length; i++) {
    var shapes = slides[i].getShapes();
    for (var j = 0; j < shapes.length; j++) {
      var textRange = shapes[j].getText();
      var keys = Object.keys(replacements);
      for (var k = 0; k < keys.length; k++) {
        var token = '{{' + keys[k] + '}}';
        textRange.replaceAllText(token, String(replacements[keys[k]]));
      }
    }

    var tables = slides[i].getTables();
    for (var t = 0; t < tables.length; t++) {
      var table = tables[t];
      for (var row = 0; row < table.getNumRows(); row++) {
        for (var col = 0; col < table.getNumColumns(); col++) {
          var cellText = table.getCell(row, col).getText();
          var keys2 = Object.keys(replacements);
          for (var m = 0; m < keys2.length; m++) {
            var token2 = '{{' + keys2[m] + '}}';
            cellText.replaceAllText(token2, String(replacements[keys2[m]]));
          }
        }
      }
    }
  }

  updateProgressArc(presentation, replacements);
  insertWorkstreamIcons(presentation, replacements);

  presentation.saveAndClose();

  copy.addEditor(userEmail);

  try {
    copy.setSharing(DriveApp.Access.DOMAIN, DriveApp.Permission.VIEW);
  } catch (domainErr) {
    Logger.log('Domain sharing skipped (may not be Workspace): ' + domainErr.message);
  }

  return 'https://docs.google.com/presentation/d/' + presentationId + '/edit';
}

function updateProgressArc(presentation, replacements) {
  var progress = parseFloat(replacements.es_metric_progress);
  if (isNaN(progress)) return;
  progress = Math.max(0, Math.min(100, progress));

  var endAngle = 180 - (progress * 1.8);
  var presentationId = presentation.getId();
  var slides = presentation.getSlides();

  for (var i = 0; i < slides.length; i++) {
    var elements = slides[i].getPageElements();
    for (var j = 0; j < elements.length; j++) {
      if (elements[j].getTitle() === 'exec_summary_progress_bar') {
        var objectId = elements[j].getObjectId();
        Slides.Presentations.batchUpdate({
          requests: [{
            updateShapeProperties: {
              objectId: objectId,
              shapeProperties: {
                pieProperties: {
                  startAngle: 180,
                  endAngle: endAngle
                }
              },
              fields: 'pieProperties.startAngle,pieProperties.endAngle'
            }
          }]
        }, presentationId);
        return;
      }
    }
  }
  Logger.log('Warning: exec_summary_progress_bar shape not found');
}

function insertWorkstreamIcons(presentation, replacements) {
  var iconTokens = ['ws_1_icon', 'ws_2_icon', 'ws_3_icon', 'ws_4_icon'];
  var needed = {};
  for (var i = 0; i < iconTokens.length; i++) {
    var iconName = replacements[iconTokens[i]];
    if (iconName) needed[iconTokens[i]] = iconName;
  }
  if (Object.keys(needed).length === 0) return;

  var library = SlidesApp.openById(ICON_LIBRARY_ID);
  var libSlides = library.getSlides();

  // Build lookup: icon name → {slideIndex, objectId}
  var iconIndex = {};
  for (var s = 0; s < libSlides.length; s++) {
    var elements = libSlides[s].getPageElements();
    for (var e = 0; e < elements.length; e++) {
      var title = elements[e].getTitle();
      if (title) iconIndex[title] = { slideIdx: s };
    }
  }

  // For each needed icon: copy the library slide containing it into the
  // target deck as a temp slide, then use the Advanced Slides API to
  // reparent the icon group onto the correct slide at the placeholder position.
  var presentationId = presentation.getId();
  var targetSlides = presentation.getSlides();

  var tokenKeys = Object.keys(needed);
  for (var t = 0; t < tokenKeys.length; t++) {
    var token = tokenKeys[t];
    var iconName = needed[token];

    if (!iconIndex[iconName]) {
      Logger.log('Icon not found in library: ' + iconName);
      continue;
    }

    // Find placeholder in target deck
    var placeholderInfo = null;
    for (var si = 0; si < targetSlides.length; si++) {
      var pageElements = targetSlides[si].getPageElements();
      for (var pe = 0; pe < pageElements.length; pe++) {
        if (pageElements[pe].getTitle() === token) {
          placeholderInfo = {
            slideIndex: si,
            slideId: targetSlides[si].getObjectId(),
            left: pageElements[pe].getLeft(),
            top: pageElements[pe].getTop(),
            width: pageElements[pe].getWidth(),
            height: pageElements[pe].getHeight(),
            element: pageElements[pe]
          };
          break;
        }
      }
      if (placeholderInfo) break;
    }

    if (!placeholderInfo) {
      Logger.log('Placeholder not found in template: ' + token);
      continue;
    }

    // Copy the library slide that has this icon into the target deck
    var srcSlide = libSlides[iconIndex[iconName].slideIdx];
    var tempSlide = presentation.appendSlide(srcSlide);

    // Find the copied icon on the temp slide
    var tempElements = tempSlide.getPageElements();
    var copiedIcon = null;
    for (var ce = 0; ce < tempElements.length; ce++) {
      if (tempElements[ce].getTitle() === iconName) {
        copiedIcon = tempElements[ce];
        break;
      }
    }

    if (!copiedIcon) {
      Logger.log('Could not find icon on copied slide: ' + iconName);
      tempSlide.remove();
      continue;
    }

    // Position and size the icon to match the placeholder
    copiedIcon.setLeft(placeholderInfo.left);
    copiedIcon.setTop(placeholderInfo.top);
    copiedIcon.setWidth(placeholderInfo.width);
    copiedIcon.setHeight(placeholderInfo.height);

    // Remove all other elements from the temp slide except the icon
    var toRemove = [];
    tempElements = tempSlide.getPageElements();
    for (var r = 0; r < tempElements.length; r++) {
      if (tempElements[r].getObjectId() !== copiedIcon.getObjectId()) {
        toRemove.push(tempElements[r]);
      }
    }
    for (var d = 0; d < toRemove.length; d++) {
      toRemove[d].remove();
    }

    // Merge: move the temp slide content onto the target slide
    // We do this by keeping the temp slide and removing the placeholder
    // Then reorder the temp slide to sit right after the target slide
    // Actually — simplest reliable approach: export icon as image, insert on target

    // Get icon as image via the Advanced API
    var iconObjectId = copiedIcon.getObjectId();
    var thumbnail = Slides.Presentations.Pages.getThumbnail(
      presentationId,
      tempSlide.getObjectId(),
      { 'thumbnailProperties.thumbnailSize': 'LARGE' }
    );

    // Insert the thumbnail image on the target slide
    var targetSlide = targetSlides[placeholderInfo.slideIndex];
    var image = targetSlide.insertImage(
      thumbnail.contentUrl,
      placeholderInfo.left,
      placeholderInfo.top,
      placeholderInfo.width,
      placeholderInfo.height
    );

    // Clean up
    placeholderInfo.element.remove();
    tempSlide.remove();

    Logger.log('Inserted icon: ' + iconName + ' as ' + token);
  }
}

function _jsonResponse(data, code) {
  var output = ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
  return output;
}

// --- Test helper: run manually in the script editor to verify ---
function testBuildDeck() {
  var testReplacements = {
    customer_name: 'Acme Corp',
    cover_subtitle: 'Q3 FY27 Partnership Review',
    partnership_start_year: '2018',
    metric_1_value: '85%',
    metric_1_label: 'Average License Utilization',
    metric_2_value: '12K',
    metric_2_label: 'Active CRM users',
    metric_3_value: '4.7/5.0',
    metric_3_label: 'CSAT score',
    imperative_1_name: 'Drive Digital Transformation',
    imperative_1_kpi_1: 'Increase platform adoption to 90%',
    imperative_1_kpi_2: 'Reduce manual processes by 40%',
    imperative_2_name: 'Unify Customer Experience',
    imperative_2_kpi_1: 'Single customer view across 5 BUs',
    imperative_2_kpi_2: 'CSAT improvement to 4.8/5.0',
    imperative_3_name: 'Accelerate AI Adoption',
    imperative_3_kpi_1: 'Deploy 3 Agentforce use cases',
    imperative_3_kpi_2: 'Reduce case resolution time 25%',
    exec_summary_subtitle: 'Strong foundation with opportunity to deepen AI and analytics adoption',
    es_card_1_headline: 'Core Strength',
    es_card_1_product: 'Sales Cloud',
    es_card_1_description: 'High adoption at 92% utilization. Power users driving pipeline visibility.',
    es_card_2_headline: 'Growth Area',
    es_card_2_product: 'Service Cloud',
    es_card_2_description: 'Deployed but underutilized. Case routing not yet optimized.',
    es_card_3_headline: 'New Deploy',
    es_card_3_product: 'Marketing Cloud',
    es_card_3_description: 'Recently launched. Email journeys live, SMS pending.',
    es_card_4_headline: 'Evaluation',
    es_card_4_product: 'Data Cloud',
    es_card_4_description: 'POC completed. Awaiting exec sign-off for full rollout.',
    es_card_5_headline: 'Planned',
    es_card_5_product: 'Agentforce',
    es_card_5_description: 'Discovery phase. Three use cases identified for Q4.',
    es_card_6_headline: 'Stable',
    es_card_6_product: 'Platform & Shield',
    es_card_6_description: 'Event monitoring active. Encryption deployed across all orgs.',
    es_metric_value: '85%',
    es_metric_label: 'Average License Utilization',
    es_metric_title: 'Strong Adoption Foundation',
    es_metric_description: 'Overall platform utilization sits at 85%, well above the industry benchmark of 68%. Sales Cloud leads at 92%, while Service Cloud presents the greatest optimization opportunity.',
    es_metric_progress: '85',
    ws_1_icon: 'brain_ai',
    ws_1_name: 'Agentforce Evaluation',
    ws_1_summary: 'Assess AI agent use cases across service and sales workflows.',
    ws_1_status: '• Discovery workshops completed\n• 3 use cases shortlisted\n• POC planned for Q4',
    ws_2_icon: 'gear_bolt',
    ws_2_name: 'Service Cloud Optimization',
    ws_2_summary: 'Improve case routing and knowledge base to reduce resolution time.',
    ws_2_status: '• Current routing rules audited\n• Knowledge gaps identified\n• New routing logic in UAT',
    ws_3_icon: 'network_nodes',
    ws_3_name: 'Data Cloud Rollout',
    ws_3_summary: 'Unify customer profiles across 5 business units.',
    ws_3_status: '• POC complete with positive results\n• Exec approval pending\n• Target go-live Q1 FY28',
    ws_4_icon: 'megaphone',
    ws_4_name: 'Marketing Cloud Expansion',
    ws_4_summary: 'Extend from email to SMS and push notification channels.',
    ws_4_status: '• Email journeys live and performing\n• SMS integration in progress\n• Push notifications scoped for Q4',
    innovation_theme_1_name: 'Agentforce',
    innovation_theme_1_description: 'AI-powered agents can automate Tier 1 service cases, reducing resolution time by 30%. Aligns directly with the cost efficiency imperative.',
    innovation_theme_2_name: 'Data Cloud + AI',
    innovation_theme_2_description: 'Unified customer profiles enable predictive analytics across business units. Foundation for the single customer view KPI.',
    innovation_theme_3_name: 'Revenue Intelligence',
    innovation_theme_3_description: 'Pipeline analytics and forecasting powered by AI. Supports the organic growth imperative with data-driven selling.',
    map_row_1_workstream: 'AI & Automation',
    map_row_1_focus_area: 'Agentforce Deployment',
    map_row_1_activities: '• Complete discovery workshops\n• Build POC for top 3 use cases\n• Present results to exec sponsor',
    map_row_1_output: 'Go/no-go decision on Agentforce by end of Q4',
    map_row_2_workstream: 'Service Optimization',
    map_row_2_focus_area: 'Case Routing & Knowledge',
    map_row_2_activities: '• Deploy new routing rules\n• Rebuild knowledge base structure\n• Train agents on updated flows',
    map_row_2_output: '25% reduction in average case resolution time',
    map_row_3_workstream: 'Data Unification',
    map_row_3_focus_area: 'Data Cloud Go-Live',
    map_row_3_activities: '• Secure exec approval\n• Onboard remaining 3 BUs\n• Validate unified profiles',
    map_row_3_output: 'Single customer view across all 5 business units',
    map_row_4_workstream: 'Channel Expansion',
    map_row_4_focus_area: 'Marketing Cloud SMS & Push',
    map_row_4_activities: '• Complete SMS integration\n• Scope push notification strategy\n• Launch cross-channel journey',
    map_row_4_output: 'Multi-channel engagement live across email, SMS, push'
  };

  var url = buildDeck(TEMPLATE_ID, 'Test QBR Deck — Acme Corp', testReplacements, Session.getActiveUser().getEmail());
  Logger.log('Test deck URL: ' + url);
}
