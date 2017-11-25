/**
 * Created by root on 8/18/17.
 */
function MarketTime(marketTime) {
  this.tradeSequence = '';
  this.tradeDate = '';
  this.tradeTime = '';
  var tradeSequenceEndIndex = marketTime.indexOf('[');
  if (tradeSequenceEndIndex != -1) {
    this.tradeSequence = marketTime.slice(0, tradeSequenceEndIndex);
    var tradeDateEndIndex = marketTime.indexOf(':');
    if (tradeDateEndIndex != -1) {
      this.tradeDate = marketTime.slice(tradeSequenceEndIndex + 1, tradeDateEndIndex);
      this.tradeTime = marketTime.slice(tradeDateEndIndex + 2, -1);
    }
  }

  this.equals = function (other) {
    return this.tradeSequence == other.tradeSequence &&
        this.tradeDate == other.tradeDate &&
        this.tradeTime == other.tradeTime;
  };

  this.lessThan = function (other) {
    if (this.equals(other)) {
      return false;
    }

    if (this.tradeSequence.length <= other.tradeSequence.length &&
        this.tradeDate.length <= other.tradeDate.length) {
      if (parseInt(this.tradeSequence) > parseInt(other.tradeSequence) ||
          (parseInt(this.tradeSequence) == parseInt(other.tradeSequence) &&
            parseInt(this.tradeDate) > parseInt(other.tradeDate)) ||
          (parseInt(this.tradeSequence) == parseInt(other.tradeSequence) &&
          parseInt(this.tradeDate) == parseInt(other.tradeDate) &&
          parseInt(this.tradeTime) > parseInt(other.tradeTime))) {
        return false;
      }
    }
    return true;
  };
}
