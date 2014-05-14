'use strict';

/* App Module */

var PiSenseApp = angular.module('PiSenseApp', [
  'ngRoute',
  'PiSenseAnimations',
  'PiSenseControllers',
  'PiSenseFilters',
  'PiSenseServices',
  'googlechart'
]);

PiSenseApp.config(['$routeProvider',
  function($routeProvider) {
    $routeProvider.
      when('/dashboard', {
          templateUrl: 'partials/dashboard.html',
          controller: 'DashboardCtrl'
      }).
      when('/network', {
          templateUrl: 'partials/network.html',
          controller: 'NetworkCtrl'
      }).
      when('/history', {
          templateUrl: 'partials/history.html',
          controller: 'HistoryCtrl'
      }).
      when('/about', {
          templateUrl: 'partials/about.html',
          controller: 'AboutCtrl'
      }).
      when('/node/:Id', {
        templateUrl: 'partials/node-detail.html',
        controller: 'NodeDetailCtrl'
      }).
      otherwise({
        redirectTo: '/dashboard'
      });
  }]);

