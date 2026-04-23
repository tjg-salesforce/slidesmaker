var TEMPLATE_ID = '1kfgV1fhspnWUE0I4uCcSi5a764X-jQamOzVZTygyad4';

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

  presentation.saveAndClose();

  copy.addEditor(userEmail);

  try {
    copy.setSharing(DriveApp.Access.DOMAIN, DriveApp.Permission.VIEW);
  } catch (domainErr) {
    Logger.log('Domain sharing skipped (may not be Workspace): ' + domainErr.message);
  }

  return 'https://docs.google.com/presentation/d/' + presentationId + '/edit';
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
    metric_1_value: '12K',
    metric_1_label: 'Active CRM users',
    metric_2_value: '98%',
    metric_2_label: 'Platform uptime SLA',
    metric_3_value: '4.7/5.0',
    metric_3_label: 'CSAT score'
  };

  var url = buildDeck(TEMPLATE_ID, 'Test QBR Deck', testReplacements, Session.getActiveUser().getEmail());
  Logger.log('Test deck URL: ' + url);
}
