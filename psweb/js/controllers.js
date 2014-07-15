'use strict';

/* Controllers */

var PiSenseControllers = angular.module('PiSenseControllers', []);

var TIME_MINUTE = 60000;
var TIME_10MINUTE = TIME_MINUTE*10;
var TIME_HOUR = TIME_MINUTE*60;
var TIME_DAY = TIME_HOUR*24;
var MAX_SPAN = TIME_DAY*1000;

PiSenseControllers.controller('AboutCtrl', ['$scope', '$routeParams', 'svcPisense',
 	function ($scope, $routeParams, svcPisense) {
  	}
 ]);

PiSenseControllers.controller('DashboardCtrl', ['$scope', '$routeParams', 'svcPisense',
  function ($scope, $routeParams, svcPisense) {
		$scope.nodes = [];

		$scope.refresh = function() {
			svcPisense.fetchNodeListWithData(function (nodelist) {
				$scope.nodes = patchNodeList(nodelist,true);
		 	});
		}

		$scope.refresh();
  	}
 ]);


PiSenseControllers.controller('NetworkCtrl', ['$scope', '$routeParams', 'svcPisense',
 	function ($scope, $routeParams, svcPisense) {
		$scope.nodes = [];

		$scope.refresh = function() {
			svcPisense.fetchNodeListWithData(function (nodelist) {
				$scope.nodes = patchNodeList(nodelist,false);
		 	});
		}

		$scope.refresh();
  	}
 ]);


PiSenseControllers.controller('NodeDetailCtrl', ['$scope', '$routeParams', 'svcPisense',
  	function($scope, $routeParams, svcPisense) {
		$scope.nodes = [];
		$scope.node = {};
		svcPisense.fetchNodeListWithData(function (nodelist) {
			$scope.nodes = patchNodeList(nodelist,false);
			for (var i = 0; i < $scope.nodes.length; i++)
				if ($scope.nodes[i].Id == $routeParams.Id) {
					$scope.node = $scope.nodes[i];
					break;
				}
	 	});
	}
]);


PiSenseControllers.controller('HistoryCtrl', ['$scope', '$routeParams', 'svcPisense',
  function ($scope, $routeParams, svcPisense) {
	$scope.nodes = [];
	$scope.nodesChecked = {};
	$scope.graphState = {};
	$scope.flatSensorList = [];
	$scope.filterProperty = "";
	$scope.propertyList = [];

	var FindPropertyInList = function (property) {
		for (var i=0; i<$scope.propertyList.length; i++)
			if ($scope.propertyList[i].property == property)
				return i;
		return -1;
	}

	svcPisense.fetchNodeListWithData(function (nodelist) {
		$scope.nodes = patchNodeList(nodelist,false);
		// Make a one dimensional list of sensors instead of node/sensor nest list
		$scope.flatSensorList = [];
		var flatListEntryNum = 0;
	  	for (var i = 0; i < nodelist.length; i++)
	  		for (var j=0; j<nodelist[i].SensorList.length; j++) {
	  			$scope.nodesChecked[flatListEntryNum] = false;
	  			$scope.flatSensorList.push({entryNum: flatListEntryNum++, nodeId:nodelist[i].Id, nickname:nodelist[i].Nickname, sensorNum:nodelist[i].SensorList[j].SensorNum, property:nodelist[i].SensorList[j].Property, units:nodelist[i].SensorList[j].Units, active:false});
	  		}
		if ($scope.flatSensorList.length != 0)
			$scope.filterProperty = $scope.flatSensorList[0].property;

		// Make a one dimensional list of all properties supported by all nodes/sensors
		$scope.propertyList = [];
		var propertyListEntryNum = 0;
  		for (var i=0; i<$scope.flatSensorList.length; i++) {
  			var j = FindPropertyInList($scope.flatSensorList[i].property)
  			if (j == -1)
  				$scope.propertyList.push({entryNum: propertyListEntryNum++, property: $scope.flatSensorList[i].property, sensorList:[i]});
  			else $scope.propertyList[j].sensorList.push(i);
		}

 	});

	$scope.chart = {};
    $scope.chart.type = "LineChart";
    $scope.chart.cssStyle = "height:400px; width:100%";
    $scope.chart.options = {
        "title": "Sensor History",
        //"theme": "maximized",
        "isStacked": "true",
        "fill": 20,
        "displayExactValues": true,
        "curveType": "function",
        "vAxis": {
            "title": "Temperature", "gridlines": {"count": 6}
        },
        "hAxis": {
            "title": "Date",
            "format": "yyyy-MM-dd HH:mm",
            "gridlines": {"count": 5},
            "minorGridlines": {"count": 3}
        }
    };
    $scope.chart.formatters = {};
	$scope.chart.data = {
		"cols": [{id: "date", label: "Date", type: "datetime"}], 
		"rows": []
	};

	var SetGraphState = function(start, end) {	// start and end are in milliseconds
		var now = new Date();
		now = Date.now();
		if (end > now) {
			start -= end - now;
			end = now
		}
		var span = end - start;
		$scope.chart.options.hAxis.format = (span > 3*TIME_DAY) ? "yyyy-MM-dd" : "yyyy-MM-dd HH:mm";

		var interval = TIME_MINUTE; 
		if (span <= (6*TIME_HOUR)) {
			interval = TIME_MINUTE;
			$scope.graphState.period = "min"
		}
		else if (span <= (2*TIME_DAY)) {
			interval = TIME_10MINUTE;
			$scope.graphState.period = "10min"
		}
		else if (span <= (12*TIME_DAY)) {
			interval = TIME_HOUR;
			$scope.graphState.period = "hour"
		}
		else {
			interval = TIME_DAY;
			$scope.graphState.period = "day"
		}
		$scope.graphState.msStart = Math.round(start/interval)*interval;
		$scope.graphState.msEnd = Math.round(end/interval)*interval;

		$scope.graphState.dtStart = new Date($scope.graphState.msStart);
		$scope.graphState.dtEnd = new Date($scope.graphState.msEnd);
	
		$scope.graphState.xData = [];
		for (var ms=$scope.graphState.msStart; ms<=$scope.graphState.msEnd; ms+=interval)
			$scope.graphState.xData.push(ms/1000);

		$scope.chart.data.rows = [];
		$scope.chart.data.cols = [{id: "date", label: "Date", type: "datetime"}];
		for (var i=0; i<$scope.flatSensorList.length; i++) {
			if ($scope.flatSensorList[i].active)
				addChartData($scope.flatSensorList[i]);
		}
	}

	var addChartData = function(flatSensorListEntry) {
		var dataSetName = flatSensorListEntry.nickname + " " + flatSensorListEntry.property;
		$scope.chart.data.cols.push({id:flatSensorListEntry.nodeId, label:dataSetName, type: "number"});
		$scope.chart.options.vAxis.title = flatSensorListEntry.property + " (" + flatSensorListEntry.units + ")";
		svcPisense.fetchHistory(flatSensorListEntry.nodeId, flatSensorListEntry.sensorNum, $scope.graphState, 
			function(history) {
				var firstSensor = ($scope.chart.data.rows.length == 0);
				var stamps = [];
				var values = [];
				if (history.length == 2) {
					stamps = history[0];	// Time stamps from the history data that was returned from the fetch
					values = history[1];	// Values from the history data that was returned from the fetch
				}
				var pos = 0;				// Will walk through the returned data
				var histLen = stamps.length;
				var val = 0;
				if (histLen != 0)
					val = values[0];

			    for (var i=0; i<$scope.graphState.xData.length; i++) {
			    	var secStamp = $scope.graphState.xData[i];
			    	if (pos < histLen) {				// if we are not past the end of the returned history data
					     if (secStamp == stamps[pos])	// if the returned data has a value for this x axis position
					    	val = values[pos++];		//   then use it and point to next value in returned data
			    	}
					if (firstSensor) {
						var d = new Date(1000 * secStamp);
				    	var r = {c:[ {v:d}, {v:val} ]};
				    	$scope.chart.data.rows.push(r);
					}
					else {
						$scope.chart.data.rows[i].c.push({v:val});
					}
			    }
			}
		);
	}

	var removeChartData = function(flatSensorListEntry) {
		for (var i=0; i<$scope.chart.data.cols.length; i++)
			if ($scope.chart.data.cols[i].id == flatSensorListEntry.nodeId) {
				$scope.chart.data.cols.splice(i,1);
				for (var j=0; j<$scope.chart.data.rows.length; j++)
			    	$scope.chart.data.rows[j].c.splice(i,1);
				break;
			}
	}

	$scope.nodeChange = function(flatSensorListEntry) {
		if ($scope.nodesChecked[flatSensorListEntry.entryNum]) {
			// Add the sensor to the chart
			flatSensorListEntry.active = true;
			addChartData(flatSensorListEntry);
		}
		else {
			// Remove the sensor from the chart
			flatSensorListEntry.active = false;
			removeChartData(flatSensorListEntry);
		}
	}

	$scope.periodChange = function(newVal) {
		var d1 = new Date();
		var d2 = new Date();
		d2 = Date.now();
		switch (newVal) {
			case 'hour':
				d1 = d2 - TIME_HOUR;
				break;
			case 'day':
				d1 = d2 - TIME_DAY;
				break;
			case '2day':
				d1 = d2 - 2*TIME_DAY;
				break;
			case 'week':
				d1 = d2 - 7*TIME_DAY;
				break;
			case 'month':
				d1 = d2 - 30*TIME_DAY;
				break;
			case '6month':
				d1 = d2 - TIME_YEAR/2;
				break;
			case 'year':
				d1 = d2 - TIME_YEAR;
				break;
			case 'all':
				d1 = d2 - 5*TIME_YEAR;
				break;
			default:
				d1 = d2 - 2*TIME_DAY;
				break;
		}
		SetGraphState(d1, d2);
	}

	$scope.zoomOut = function() {
		var start = $scope.graphState.dtStart.getTime();
		var end = $scope.graphState.dtEnd.getTime();
		var span = end - start;
		var center = start + span / 2;
		span = span * 2;
		if (span > MAX_SPAN)
			span = MAX_SPAN;
		start = center - span / 2;
		end = center + span / 2;
		SetGraphState(start, end);
	}

	$scope.zoomIn = function() {
		var start = $scope.graphState.dtStart.getTime();
		var end = $scope.graphState.dtEnd.getTime();
		var span = end - start;
		var center = start + span / 2;
		span = span * 0.5;
		if (span  < TIME_HOUR)
			span = TIME_HOUR;
		start = center - span / 2;
		end = center + span / 2;
		SetGraphState(start, end);
	}

	$scope.panLeft = function() {
		var start = $scope.graphState.dtStart.getTime();
		var end = $scope.graphState.dtEnd.getTime();
		var span = end - start;
		var center = start + span / 2;
		center = center - (span * 0.25);
		start = center - span / 2;
		end = center + span / 2;
		SetGraphState(start, end);
	}

	$scope.panRight = function() {
		var start = $scope.graphState.dtStart.getTime();
		var end = $scope.graphState.dtEnd.getTime();
		var span = end - start;
		var center = start + span / 2;
		center = center + (span * 0.25);
		start = center - span / 2;
		end = center + span / 2;
		SetGraphState(start, end);
	}

	$scope.periodChange('2day')
  } ]);


function patchNodeList(nodelist,short) {
  	for (var i = 0; i < nodelist.length; i++) {
		nodelist[i].LastSignalStrength = Math.ceil(6 * (nodelist[i].LastRssi - 165) / (233 - 165));
		nodelist[i].SensorCount = nodelist[i].SensorList.length;
  		if (isNaN(nodelist[i].LastDateTime))
			nodelist[i].LastDateTimeAgo = (short ? "?" : "Unknown");
		else {
			var d = new Date(1000 * nodelist[i].LastDateTime);
			nodelist[i].LastDateTimeAgo = timeSince(d,short);
		}
  	}
	return nodelist;	
}


function timeSince(date,short) {
	var seconds = Math.floor((new Date() - date) / 1000);
	var interval = Math.floor(seconds / 31536000);
	if (interval > 1) return interval + (short ? "y" : " years ago");
	interval = Math.floor(seconds / 2592000);
	if (interval > 1) return interval + (short ? "mo" : " months ago");
	interval = Math.floor(seconds / 86400);
	if (interval > 1) return interval + (short ? "d" : " days ago");
	interval = Math.floor(seconds / 3600);
	if (interval > 1) return interval + (short ? "h" : " hours ago");
	interval = Math.floor(seconds / 60);
	if (interval > 1) return interval + (short ? "m" : " minutes ago");
	return Math.floor(seconds) + (short ? "s" : " seconds ago");
}

