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

  // .factory('cmseTwitterService', ['$resource', function ($resource) {
  //   return $resource('/twitter/', {}, {
  //     query: {method: 'GET'}})
  // }])

  .controller('cmseSocialCtrl', 
    ['$scope', '$log', '$http', 'cmseInstagramService', 
    function($scope, $log, $http, cmseInstagramService) {
      $scope.loading = true;
      $scope.instagram = []

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
      var chunkSize = 4;
      function chunk(arr, size) {
        var newArr = [];
        for (var i=0; i<arr.length; i+=size) {
        newArr.push(arr.slice(i, i+size));
        }
        return newArr;
      }

      cmseInstagramService.get(function(data) {
        $scope.instagram = data;
        $log.log($scope.instagram);
        $scope.chunkedData = chunk($scope.instagram.data, chunkSize);
        $log.log($scope.chunkedData);
        $scope.loading = false;
      });
  }])

  .directive('cmseLoading', function() {
    return {
      templateUrl: 'loading-partial.html'
    };
  });
})();
