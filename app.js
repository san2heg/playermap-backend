require('dotenv').config();
var express = require('express');
var morgan = require('morgan');
var MongoClient = require('mongodb').MongoClient;
var app = express();

// Logging
app.use(morgan('dev'));

// Serve static headshots
app.use(express.static('public'));

// Connect to database
MongoClient.connect('mongodb+srv://san2heg:'+process.env.DB_PASS+'@nba-trade-map-aoy8h.mongodb.net/test?retryWrites=true', { useNewUrlParser: true }, function (err, client) {
  if (err) throw err
  let db = client.db('players')

  // Endpoint for getting all player rankings
  app.get('/players/all', function(req, res) {
    res.send('All players');
  });

  // Endpoint for getting player rankings by year
  app.get('/players/:year', function(req, res) {
    res.send('Players for ' + req.params['year']);
  });
})

app.listen(3000);
