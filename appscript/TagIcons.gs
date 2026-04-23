function tagAllIcons() {
  var LIBRARY_ID = '1i_aLUcHQwnPjEAFIlK6x4jmuKZ2PD1J5eDYxyNEyIew';
  var deck = SlidesApp.openById(LIBRARY_ID);
  var slides = deck.getSlides();

  // Slide 2 (index 1)
  var s2 = [
    // Row 1
    'airplane', 'bell', 'settings_gear', 'search_target', 'bar_chart_up',
    'hand_touch', 'computer_monitor', 'puzzle_key', 'trophy', 'chart_down', 'book_open',
    // Row 2
    'brain', 'clock_gear', 'leaf_head', 'brick_wall', 'hand_cursor',
    'server', 'buildings', 'calendar', 'calendar_date', 'truck', 'car',
    // Row 3
    'cassette', 'printer', 'clipboard_doc', 'timer', 'cloud',
    'plant_sprout', 'coffee_mug', 'no_sign', 'monitor_chat', 'chat_bubble', 'target_bullseye'
  ];

  // Slide 3 (index 2)
  var s3 = [
    // Row 1
    'team_group', 'org_chart', 'network_nodes', 'molecule', 'cylinder_db',
    'flag_send', 'venn_diagram', 'lock_secure', 'document_copy', 'wifi_person', 'sparkle_burst',
    // Row 2
    'gear_bolt', 'person_badge', 'calendar_star', 'calendar_check', 'fast_forward',
    'rocket', 'funnel_filter', 'celebration', 'branch_fork', 'grid_blocks', 'refresh_cycle',
    // Row 3
    'mountain_flag', 'heart', 'emoji_face', 'hourglass', 'podium',
    'lightbulb', 'pen_tool', 'calendar_1', 'globe_gear', 'laptop_devices', 'chart_laptop'
  ];

  // Slide 4 (index 3)
  var s4 = [
    // Row 1
    'scales_justice', 'lightbulb_idea', 'checklist', 'compass_target', 'satellite_person',
    'magnify_lock', 'circle_person', 'badge_people', 'wrench_key', 'magnify_search', 'gear_inspect',
    // Row 2
    'medal_ribbon', 'code_branch', 'brain_ai', 'money_bag', 'equalizer_bars',
    'team_meeting', 'conveyor_ship', 'inbox_tray', 'vinyl_record', 'phone_tablet', 'clipboard_edit',
    // Row 3
    'people_network', 'pen_writing', 'phone_sync', 'arrow_right', 'clock_no',
    'astronaut', 'rocket_launch', 'star_badge', 'browser_window', 'checklist_gear', 'settings_cog'
  ];

  // Slide 5 (index 4)
  var s5 = [
    // Row 1
    'shield_check', 'globe_web', 'cart', 'cart_add', 'megaphone',
    'gateway', 'speech_bubble', 'chat_person', 'pie_chart', 'target_rings', 'upload_box',
    // Row 2
    'puzzle_piece', 'robot_hand', 'headset', 'record_button', 'list_detail',
    'stamp_machine', 'lightning_bolt', 'ticket', 'frame_window', 'handshake', 'workflow_nodes',
    // Row 3
    'cycle_refresh', 'calendar_grid', 'user_settings', 'checkmark', 'clipboard_check',
    'agent_support', 'timer_clock', 'warning_triangle', 'monitor_error', 'pen_edit', 'magic_wand'
  ];

  var allMaps = [
    { slideIndex: 1, names: s2 },
    { slideIndex: 2, names: s3 },
    { slideIndex: 3, names: s4 },
    { slideIndex: 4, names: s5 }
  ];

  var ROW_Y = [249, 425, 602];
  var COL_X = [95, 211, 327, 444, 560, 677, 793, 910, 1026, 1143, 1259];

  for (var m = 0; m < allMaps.length; m++) {
    var slide = slides[allMaps[m].slideIndex];
    var names = allMaps[m].names;
    var elements = slide.getPageElements();

    var nameIndex = 0;
    for (var r = 0; r < ROW_Y.length; r++) {
      for (var c = 0; c < COL_X.length; c++) {
        var targetX = COL_X[c];
        var targetY = ROW_Y[r];
        var name = names[nameIndex];
        nameIndex++;

        for (var e = 0; e < elements.length; e++) {
          var el = elements[e];
          if (el.getPageElementType() != SlidesApp.PageElementType.GROUP) continue;
          var elX = Math.round(el.getLeft());
          var elY = Math.round(el.getTop());
          if (Math.abs(elX - targetX) < 10 && Math.abs(elY - targetY) < 10) {
            el.setTitle(name);
            Logger.log('Tagged: ' + name + ' (slide ' + (allMaps[m].slideIndex + 1) + ', pos ' + elX + ',' + elY + ')');
            break;
          }
        }
      }
    }
  }

  deck.saveAndClose();
  Logger.log('Done — all icons tagged.');
}
