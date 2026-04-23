function inspectLibrary() {
  var deck = SlidesApp.openById('1i_aLUcHQwnPjEAFIlK6x4jmuKZ2PD1J5eDYxyNEyIew');
  var slides = deck.getSlides();
  for (var i = 0; i < slides.length; i++) {
    var elements = slides[i].getPageElements();
    Logger.log('--- Slide ' + (i+1) + ': ' + elements.length + ' elements ---');
    for (var j = 0; j < elements.length; j++) {
      var el = elements[j];
      var type = el.getPageElementType();
      var childCount = '';
      if (type == SlidesApp.PageElementType.GROUP) {
        childCount = ' | children=' + el.asGroup().getChildren().length;
      }
      var info = '  [' + j + '] id=' + el.getObjectId();
      info += ' | type=' + type;
      info += ' | title="' + el.getTitle() + '"';
      info += ' | desc="' + el.getDescription() + '"';
      info += ' | pos=(' + Math.round(el.getLeft()) + ',' + Math.round(el.getTop()) + ')';
      info += ' | size=(' + Math.round(el.getWidth()) + 'x' + Math.round(el.getHeight()) + ')';
      info += childCount;
      Logger.log(info);
    }
  }
}
