'use strict';

/* Services */

var PiSenseServices = angular.module('PiSenseServices', ['ngResource']);

PiSenseServices.factory('Phone', ['$resource',
  function($resource){
    return $resource('phones/:phoneId.json', {}, {
      query: {method:'GET', params:{phoneId:'phones'}, isArray:true}
    });
  }]);


var USE_REALDATA = 1


PiSenseServices.factory('svcPisense', function ($resource) {
    return {
        fetchNodeListWithData: function (callback) {
            if (USE_REALDATA) {
                var api = $resource('data/nodelistwithdata&callback=JSON_CALLBACK', {}, { fetch: { method: 'JSONP'} });
                api.fetch(function (response) {
                    callback(response.query);
                });
            }
            else {
                var fakedata = [
                    {Id:'99999999', Nickname:'Test Node 9', Model:"PiSense Enviro", LastRssi:200, LastDateTime:1, LastBattery:75, 
                     Manufacturer:'Porcupine Electronics', HwVersion:'v3', FwVersion: '1.04',
                     SensorList:[
                        {Property:'Temperature', Units:'Deg C',  LastValue:'27.3', Minimum:'0', Maximum:'100'},
                        {Property:'Humidity',    Units:'% RH',   LastValue:'65',   Minimum:'0', Maximum:'100'},
                        {Property:'Pressure',    Units:'mbar',   LastValue:'993',  Minimum:'0', Maximum:'100'},
                        {Property:'Light',       Units:'% full', LastValue:'43',   Minimum:'0', Maximum:'100'}
                     ]},
                    {Id:'88888888', Nickname:'Test Node 8', Model:"PiSense Enviro", LastRssi:220, LastDateTime:1, LastBattery:65,
                     Manufacturer:'Porcupine Electronics', HwVersion:'v3', FwVersion: '1.04',
                     SensorList:[
                        {Property:'Temperature', Units:'Deg C',  LastValue:'22.1', Minimum:'0', Maximum:'100'},
                        {Property:'Humidity',    Units:'% RH',   LastValue:'54',   Minimum:'0', Maximum:'100'},
                        {Property:'Pressure',    Units:'mbar',   LastValue:'1002', Minimum:'0', Maximum:'100'},
                        {Property:'Light',       Units:'% full', LastValue:'78',   Minimum:'0', Maximum:'100'}
                     ]}
                ];
                callback(fakedata);
            }
        },
        fetchNodeList: function (callback) {
            var api = $resource('data/nodelist&callback=JSON_CALLBACK', {}, { fetch: { method: 'JSONP'} });
            api.fetch(function (response) {
                callback(response.query);
            });
        },
        fetchSensorData: function (callback) {
            var api = $resource('data/sensordata&callback=JSON_CALLBACK', {}, { fetch: { method: 'JSONP'} });
            api.fetch(function (response) {
                callback(response.query);
            });
        },
        fetchHistory: function (nodeId, sensorNum, graphState, callback) {
            if (USE_REALDATA) {
                // API: data/history/<nodeId>/<sensorNum>/<period>/<mxa>/<start>/<end>     (start/end are in seconds, m=min/x=max/a=avg)
                var api = $resource('data/history/'+nodeId+'/'+sensorNum+'/'+graphState.period+'/a/'+graphState.msStart/1000+'/'+graphState.msEnd/1000+'&callback=JSON_CALLBACK', {}, { fetch: { method: 'JSONP'} });
                api.fetch(function (response) {
                    callback(response.query);
                });
            }
            else {
                var fakeoffset = sensorNum;
                var fakedata = [];
                for (var i=0; i<graphState.xData.length; i++) {
                    fakedata[i] = fakeoffset + 20 + 10*Math.cos(graphState.xData[i]/(60*60*24))+4*Math.cos(graphState.xData[i]/(60*60*(fakeoffset+1)));
                }
                callback(fakedata);
            }
        }
    }
});
