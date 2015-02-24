var fs = require('fs');

module.exports = function loadJSON(filename) {

  fs.readFile(filename, function (err, data) {
    if (err) throw err;
    return data.toString();
  });
};

// /Users/sean/Sync/cornell/CM/explorer/data/instagram-seannnnnnnnnnnn-10666196.json
