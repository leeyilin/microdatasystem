/**
 * Created by root on 7/20/17.
 */
var nextIndex = 1;
$(function () {
  function setNextAttr(myElement) {
    var originalName = myElement.attr('name');
    var braketIndex = originalName.indexOf('[');
    var nextName = originalName.substr(0, braketIndex + 1) + nextIndex + "]";
    myElement.attr('name', nextName);

    var originalID = myElement.attr('id');
    braketIndex = originalID.indexOf('[');
    var nextID = originalID.substr(0, braketIndex + 1) + nextIndex + "]";
    myElement.attr('id', nextID);
    myElement.val(1861);
  }

  $(document).on('click', '.btn-add', function (e) {
    e.preventDefault();
    var controlForm = $('.controls form:first'),
        currentEntry = $(this).parents('.entry:first'),
        newEntry = $(currentEntry.clone()).appendTo(controlForm);

    nextIndex += 1;
    setNextAttr(newEntry.find('input:first'));
    setNextAttr(newEntry.find('input:last'));
    newEntry.find('input:first').val('');
    // The default port is 1861.
    newEntry.find('input:last').val(1861);

    controlForm.find('.entry:not(:last) .btn-add')
        .removeClass('btn-add').addClass('btn-remove')
        .removeClass('btn-success').addClass('btn-danger')
        .html('<span class="glyphicon glyphicon-minus"></span>');
  }).on('click', '.btn-remove', function (e) {
    $(this).parents('.entry:first').remove();
    e.preventDefault();
    return false;
  });
});