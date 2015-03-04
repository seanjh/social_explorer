(function() {
  'use strict';

  angular.module('SocialExplorerApp', ['ngResource'])
  .config(function($interpolateProvider){
    $interpolateProvider.startSymbol('{[{').endSymbol('}]}');
  })

  .factory('cmseInstagramService', ['$http', function ($http) {
    return {
      get: function (callback) {
        $http.get('/instagram').success(function (data) {
          callback(data);
        });
      }
    };
  }])

  .factory('cmseTwitterService', ['$resource', function ($resource) {
    return $resource('/twitter/');
  }])

  .filter('getLabelName', function () {
    return function(label, scope) {
      if (scope.instagram.labels && scope.instagram.labels[label]) {
          return scope.instagram.labels[label].name;
        } else {
          return 'N/A';
        }
    };
  })

  .controller('cmseSocialCtrl', 
    ['$scope', '$log', '$http', 'cmseInstagramService', 'cmseTwitterService',
    function($scope, $log, $http, cmseInstagramService, cmseTwitterService) {
      $scope.loading = true;
      $scope.instagram = {}
      $scope.chunkedData = {};
      $scope.twitter = {};
      var chunkSize = 4;

      function partitionByLabel(arr) {
        var result = {}
        var data;
        var label;
        for (var i=0; i<arr.length; i++) {
          data = arr[i];
          label = data.location.label;
          if (data && label !== null && label >= 0) {
            if (!result[label]) {
              // $log.log('Creating new object for label ' + label);
              result[label] = [];
            }
            // $log.log('Inserting object under label ' + label);
            result[label].push(data);
          }
        }
        return result;
      }

      $scope.getImageURL = function(media) {
        if (media.thumbnail) return media.thumbnail.url;
        else if (media.low_resolution) return media.low_resolution.url;
        else if (media.standard_resolution) return media.standard_resolution.url;
      };

      $scope.isImage = function (media) {
        return media.thumbnail;
      };

      $scope.getVideoURL = function (media) {
        if (media.low_bandwidth) return media.low_bandwidth.url;
        else if (media.low_bandwidth) return media.low_bandwidth.url;
        else if (media.standard_resolution) return media.standard_resolution.url;
      }

      // TODO: CITE http://stackoverflow.com/posts/21653981/revisions
      function chunk(arr, size) {
        var newArr = [];
        for (var i=0; i<arr.length; i+=size) {
        newArr.push(arr.slice(i, i+size));
        }
        return newArr;
      }

      cmseInstagramService.get(function(resp) {
        var key;
        $scope.instagram = resp;
        $log.log('Raw data: ' + $scope.instagram);
        var labelData = partitionByLabel(resp.data);
        $log.log(labelData);
        for (key in labelData) {
          $log.log('Getting chunks for label ' + key);
          $scope.chunkedData[key] = chunk(labelData[key], chunkSize);
        }
        $log.log('Chunked data' + $scope.chunkedData);
        $scope.loading = false;

        var sample, query, lat, lon;
        for (key in labelData) {
          sample = labelData[key][0];
          // $log.log('Using sample instagram data');
          // $log.log(sample);
          lat = sample.location.latitude;
          lon = sample.location.longitude;
          query = {latitude: lat, longitude: lon, label: key};
          $log.log(query);
          cmseTwitterService.get(query, function (tweet_meta) {
            // $log.log('Twitter data for label ' + key);
            // $log.log(tweet_meta);
            $scope.twitter[key] = tweet_meta;
          });
        }
        $log.log($scope.twitter);
      });
  }])

  .directive('cmseLoading', function() {
    return {
      templateUrl: 'loading-partial.html'
    };
  });
})();
