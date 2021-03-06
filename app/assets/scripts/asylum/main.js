"use strict";

var categories = [];
var features = [];
var requirements = [];
var markers = [];

var buttonClick = function (button, list) {
  $(button).click(function() {
    var item = $(this).attr('id');
    var index = jQuery.inArray('.' + item, list);
    if (index > -1) {
      list.splice(index, 1);
    } else {
      list.push('.' + item);
    }
    displayResources();
  });
};

var displayResources = function() {
  $('.resource').removeClass("active"); // hide all resources
  $('#hidden-buttons').html('');

  if (map) {
    hideAllMapPoints();
  }
  var areSelectedCategories = categories.length > 0;
  var areSelectedRequirements = requirements.length > 0;

  if (areSelectedCategories || features.length > 0) {
    var toDisplay = $('.resource' + features.join('')); //

    if (areSelectedCategories) {
      toDisplay = toDisplay.filter(categories.join(', '));
    }

    if (areSelectedRequirements) {
      toDisplay = toDisplay.not(requirements.join(', '));
    }

    toDisplay.addClass("active"); // shows appropriate resources e.g., $('.resource.translation').filter('.dental-care, .hygiene')')
    if (map) {
      displaySelectedMapPoints(toDisplay);
    }
  }

  // handle showing checked options as buttons in print view
  categories.forEach(function(category) {
    // first get attributes of this button
    var $elem = $('#' + category.substring(1));
    if($elem.is(":checkbox")) {
      var label = $elem.data('label');
      var icon = $elem.data('ic');

      var htmlString = '<button type="button" class="btn-category btn btn-default active" data-toggle="button"><span class="icon-' + icon + ' btn-icon"></span>' + label + '</button>';

      $(htmlString).appendTo('#hidden-buttons');
    }
  });
}

var geocoder;
var map;
var infoWindow;


var hideAllMapPoints = function() {
  infoWindow.close();
  for (var key in markers) {
    if (markers.hasOwnProperty(key)) {
      markers[key].setVisible(false);
    }
  }
}

var displaySelectedMapPoints = function(toDisplay) {
  toDisplay.find('.map-point').each(function() {
    var address = $(this).attr('address');
    markers[address].setVisible(true);
  });
}

function googleTranslateElementInit() {
  new google.translate.TranslateElement({pageLanguage: 'en', gaTrack: true, gaId: 'UA-76058112-1'}, 'google_translate_element');
}

function initMap() {
  // find center of map
  var avLat = 0;
  var avLng = 0;
  var numThings = 0;
  $('.map-point').each(function() {
    var s_lat = $(this).attr('lat');
    var s_lng = $(this).attr('long');

    var lat = parseFloat(s_lat);
    var lng = parseFloat(s_lng);

    if(!!lat && !!lng) {
      avLat += lat;
      avLng += lng;
      numThings++;
    }
  });

  avLat /= numThings;
  avLng /= numThings;

  map = new google.maps.Map(document.getElementById('map'), {
    //center: {lat: 47.608, lng: -122.335},
    center: {lat: avLat, lng: avLng},
    zoom: 11
  });
  geocoder = new google.maps.Geocoder();
  infoWindow = new google.maps.InfoWindow({});

  // loop through and plot all map points
  $('.map-point').each(function() {
    var that = $(this);
    var address = that.attr('address');
    var lat = that.attr('lat');
    var long = that.attr('long');
    // if lat and long are defined, create marker using coords
    if (lat && long) {
      var marker = new google.maps.Marker({
        map: map,
        position: {
          lat : parseFloat(lat),
          lng : parseFloat(long)
        }
      });
      google.maps.event.addListener(marker, 'click', function(){
        infoWindow.setContent(that.html());
        infoWindow.open(map, marker);
      });

      markers[address] = marker;
      markers[address].setVisible(false);
    }
    // else, geocode address to create marker
    else {
      geocoder.geocode({'address' : address}, function(results, status) {
        if (status === google.maps.GeocoderStatus.OK) {
          var marker = new google.maps.Marker({
            map: map,
            position: results[0].geometry.location
          });

          google.maps.event.addListener(marker, 'click', function(){
            infoWindow.setContent(that.html());
            infoWindow.open(map, marker);
          });

          markers[address] = marker;
          markers[address].setVisible(false);
        }
      });
    }
  });
//  // try geolocation
//  if (navigator.geolocation) {
//    navigator.geolocation.getCurrentPosition(function(position) {
//        var pos = {
//            lat: position.coords.latitude,
//            lng: position.coords.longitude
//        };
//
//        infoWindow.setPosition(pos)
//        infoWindow.setContent('Location found.');
//        map.setCenter(pos);
//    }, function() {
//            handleLocationError(true, infoWindow, map.getCenter());
//    });
//  } else {
//    // browser doesn't support geolocation
//    handleLocationError(false, infoWindow, map.getCenter());
//    }
//}
//function handleLocationError(browserHasGeolocation, infoWindow, pos) {
//   infoWindow.setPosition(pos);
//   infoWindow.setContent(browserHasGeolocation ?
//                         'Error: The Geolocation service failed.' :
//                         'Error: Your browser doesn\'t support geolocation.');
}


$(document).ready(function(){
  $('.resource-header').click(function() {
    $(this).next('.resource-content').toggle();
  });

  buttonClick('.btn-filter', features);
  buttonClick('.btn-category', categories);
  buttonClick('.checkbox-category', categories);
  buttonClick('.checkbox-requirement', requirements);

  $('.dropdown-menu').click(function(e) {
    e.stopPropagation();
  });

});
