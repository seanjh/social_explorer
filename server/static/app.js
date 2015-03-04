(function() {
  'use strict';

  angular.module('SocialExplorerApp', [])
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

  .filter('getLabelName', function () {
    return function(label, scope) {
      if (scope.instagram.labels && scope.instagram.labels[label]) {
          return scope.instagram.labels[label].name;
        } else {
          return 'N/A';
        }
    };
  })

  .factory('cmseTwitterService', ['$resource', function ($resource) {
    return $resource('/twitter', {}, {});
  }])

  .controller('cmseSocialCtrl', 
    ['$scope', '$log', '$http', 'cmseInstagramService', 
    function($scope, $log, $http, cmseInstagramService) {
      $scope.loading = true;
      $scope.instagram = {}
      $scope.chunkedData = {};
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

      // $scope.getLabelName = function(label) {
      //   if ($scope.instagram.labels && $scope.instagram.labels[label]) {
      //     return $scope.instagram.labels[label].name;
      //   } else {
      //     return 'N/A';
      //   }
      // }

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
        $scope.instagram = resp;
        $log.log('Raw data: ' + $scope.instagram);
        var labelData = partitionByLabel(resp.data);
        $log.log(labelData);
        for (var key in labelData) {
          $log.log('Getting chunks for label ' + key);
          $scope.chunkedData[key] = chunk(labelData[key], chunkSize);
        }
        $log.log('Chunked data' + $scope.chunkedData);
        $scope.loading = false;
      });
  }])

  .directive('cmseLoading', function() {
    return {
      templateUrl: 'loading-partial.html'
    };
  });
})();
