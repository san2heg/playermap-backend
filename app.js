require('dotenv').config();
var express = require('express');
var morgan = require('morgan');
var path = require('path');
var MongoClient = require('mongodb').MongoClient;
var app = express();

// Logging
app.use(morgan('dev'));

// Serve static headshots
app.use(express.static('public'));

// Serve react frontend
app.use(express.static(path.join(__dirname, 'build')));

app.get('/', function(req, res) {
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

// Connect to database
MongoClient.connect('mongodb+srv://san2heg:'+process.env.DB_PASS+'@nba-trade-map-aoy8h.mongodb.net/test?retryWrites=true', { useNewUrlParser: true }, function (err, client) {
  if (err) throw err;
  var db = client.db('players');
  var player_collection = db.collection('rankings');

  // Endpoint for getting all player rankings
  app.get('/players/all', function(req, res, next) {
    player_collection.find().toArray(function(err, result) {
      if (err) next(err);
      if (result == null) res.status(400).json({});
      else {
        player_table = {};
        for (var item of result) {
          player_table[item['year']] = item['players'];
        }
        res.json(player_table);
      }
    });
  });

  // Endpoint for getting player rankings by year
  app.get('/players/:year', function(req, res) {
    player_collection.findOne({'year': parseInt(req.params['year'])}, function(err, item) {
      if (err) next(err);
      if (item == null) res.status(400).json({});
      else {
        res.json(item['players']);
      }
    })
  });
})

app.listen(5000);
