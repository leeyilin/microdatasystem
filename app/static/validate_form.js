$(document).ready(function () {
  var stockMessageIDs = [8101, 8103, 8104, 8105, 8112, 8113, 8115, 8117, 8118, 8119];
  $('form#basic_stock_data').submit(function (event) {
    var tmpID = parseInt($('select#message_id').val());
    if (stockMessageIDs.indexOf(tmpID) != -1) {
      var tmpStockID = $('input#stock_id').val();
      if (tmpStockID == '') {
        // Make it warn in a more friendly way later.
        alert('Stock ID is required!');
        return false;
      }
    }
    return true;
  });

  $("#my_unique_ul1 li").on("click", function () {
    var content = $(this).text();
    $("#ip_list").val(content);
  });

  $(document).on('change', 'input', function () {
    if ($(this).attr('id') == 'port') {
      var portValue = $(this).val();
      if (isNaN(portValue) || portValue < 0 || portValue > 65536) {
        $(this).val(1861);
      }
    } else if ($(this).attr('id') == 'ip_list') {
      if ($(this).val().length > 15) {
        $(this).val('114.80.234.100');
      }
    }
  });

  $("#my_unique_ul2 li").on("click", function () {
    var content = $(this).text();
    $("#market_name").val(content);
  });

  $("#my_unique_ul3 li").on("click", function () {
    var stock_id = $(this).text();
    $("#stock_id").val(stock_id);
  });

});
/**
 * Created by root on 8/2/17.
 */
