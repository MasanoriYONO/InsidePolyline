(function ($)
{
    $.widget("ui.gmap",
    {
        options :
        {
            center : (google.maps) ? new google.maps.LatLng(0.0, 0.0) : null, mapTypeId : (google.maps) ? google.maps.MapTypeId.ROADMAP : null,
            zoom : 5
        },
        _create : function ()
        {
            this.options.center = this._latLng(this.options.center);
            var a = this.element;
            this.id = a.attr('id');
            this.instances = [];
            var b = this.instances[a.attr('id')] = {
                map : new google.maps.Map(a[0], this.options), markers : [], services : [], overlays : []
            };
            google.maps.event.addListenerOnce(b.map, 'bounds_changed', function ()
            {
                a.trigger('init', b.map)
            });
            return $(b.map);
        },
        _setOption : function (a, b)
        {
            var c = this.get('map');
            jQuery.extend(this.options, {
                'center' : c.getCenter(), 'mapTypeId' : c.getMapTypeId(), 'zoom' : c.getZoom()
            });
            if (a && b) {
                $.Widget.prototype._setOption.apply(this, arguments)
            };
            c.setOptions(this.options)
        },
        addBounds : function (a)
        {
            this.get('bounds', new google.maps.LatLngBounds()).extend(this._latLng(a));
            this.get('map').fitBounds(this.get('bounds'))
        },
        addControl : function (a, b)
        {
            this.get('map').controls[b].push(this._unwrap(a))
        },
        addMarker : function (a, b, c)
        {
            var d = this.get('map');
            var c = c || google.maps.Marker;
            a.position = (a.position) ? this._latLng(a.position) : null;
            var e = new c(jQuery.extend({
                'map' : d, 'bounds' : false
            }, a));
            var f = this.get('markers', []);
            if (e.id) {
                f[e.id] = e
            }
            else {
                f.push(e)
            }
            if (e.bounds) {
                this.addBounds(e.getPosition())
            }
            this._call(b, d, e);
            return $(e);
        },
        addInfoWindow : function (a, b)
        {
            var c = new google.maps.InfoWindow(a);
            this._call(b, c);
            return $(c);
        },
        clear : function (a)
        {
            this._c(this.get(a));
            this.set(a, [])
        },
        _c : function (a)
        {
            for (b in a)
            {
                if (a[b]instanceof google.maps.MVCObject) {
                    google.maps.event.clearInstanceListeners(a[b]);
                    a[b].setMap(null)
                }
                else if (a[b]instanceof Array) {
                    this._c(a[b])
                }
                a[b] = null;
            }
        },
        findMarker : function (a, b, c, d)
        {
            var e = this.get('markers');
            for (f in e)
            {
                var g = (c && e[f][a]) ? (e[f][a].split(c).indexOf(b) > -1) : (e[f][a] === b);
                this._call(d, e[f], g)
            }
        },
        get : function (a, b)
        {
            var c = this.instances[this.id];
            if (!c[a])
            {
                if (a.indexOf('>') > -1)
                {
                    var e = a.replace(/ /g, '').split('>');
                    for (var i = 0; i < e.length; i++) {
                        if (!c[e[i]]) {
                            if (b) {
                                c[e[i]] = ((i + 1) < e.length) ? [] : b
                            }
                            else {
                                return null;
                            }
                        }
                        c = c[e[i]]
                    }
                    return c
                }
                else if (b && !c[a]) {
                    this.set(a, b)
                }
            }
            return c[a];
        },
        openInfoWindow : function (a, b)
        {
            this.get('iw', new google.maps.InfoWindow).setOptions(a);
            this.get('iw').open(this.get('map'), this._unwrap(b))
        },
        set : function (a, b)
        {
            this.instances[this.id][a] = b;
        },
        refresh : function ()
        {
            $(this.get('map')).triggerEvent('resize');
            this._setOption()
        },
        destroy : function ()
        {
            $.Widget.prototype.destroy.call(this);
            this.clear('markers');
            this.clear('services');
            this.clear('overlays', true);
            var a = this.instances[this.id];
            for (b in a) {
                a[b] = null;
            }
        },
        _call : function (a)
        {
            if ($.isFunction(a)) {
                a.apply(this, Array.prototype.slice.call(arguments, 1))
            }
        },
        _latLng : function (a)
        {
            if (a instanceof google.maps.LatLng) {
                return a
            }
            else {
                var b = a.replace(' ', '').split(',');
                return new google.maps.LatLng(b[0], b[1]);
            }
        },
        _unwrap : function (a)
        {
            if (!a) {
                return null
            }
            else if (a instanceof jQuery) {
                return a[0]
            }
            else if (a instanceof Object) {
                return a
            }
            return $('#' + a)[0];
        },
        displayDirections : function (a, b, c)
        {
            var d = this;
            var e = this.get('services > DirectionsService', new google.maps.DirectionsService());
            var f = this.get('services > DirectionsRenderer', new google.maps.DirectionsRenderer());
            f.setOptions(b);
            e.route(a, function (g, h)
            {
                if (h === 'OK') {
                    if (b.panel) {
                        f.setDirections(g)
                    }
                    f.setMap(d.get('map'))
                }
                else {
                    f.setMap(null)
                }
                d._call(c, g, h)
            })
        },
        displayStreetView : function (a, b)
        {
            this.get('map').setStreetView(this.get('services > StreetViewPanorama', new google.maps.StreetViewPanorama(this._unwrap(a),
            b)))
        },
        search : function (a, b)
        {
            this.get('services > Geocoder', new google.maps.Geocoder()).geocode(a, b)
        },
        addShape : function (a, b)
        {
            return $(this.get('overlays > ' + a, []).push(new google.maps[a](jQuery.extend( {
                'map' : this.get('map')
            }, b))))
        },
        loadFusion : function (a, b)
        {
            ((!b) ? this.get('overlays > FusionTablesLayer', new google.maps.FusionTablesLayer()) : this.get('overlays > FusionTablesLayer',
            new google.maps.FusionTablesLayer(b, a))).setOptions(jQuery.extend({
                'map' : this.get('map')
            }, a))
        },
        loadKML : function (a, b, c)
        {
            this.get('overlays > ' + a, new google.maps.KmlLayer(b, jQuery.extend({
                'map' : this.get('map')
            }, c)))
        }
    });
    jQuery.fn.extend(
    {
        click : function (a)
        {
            return this.addEventListener('click', a);
        },
        rightclick : function (a)
        {
            return this.addEventListener('rightclick', a);
        },
        dblclick : function (a)
        {
            return this.addEventListener('dblclick', a);
        },
        mouseover : function (a)
        {
            return this.addEventListener('mouseover', a);
        },
        mouseout : function (a)
        {
            return this.addEventListener('mouseout', a);
        },
        drag : function (a)
        {
            return this.addEventListener('drag', a);
        },
        dragend : function (a)
        {
            return this.addEventListener('dragend', a);
        },
        triggerEvent : function (a)
        {
            google.maps.event.trigger(this [0], a)
        },
        addEventListener : function (a, b)
        {
            if (google.maps && this [0]instanceof google.maps.MVCObject) {
                google.maps.event.addListener(this [0], a, b)
            }
            else {
                this.bind(a, b)
            }
            return this;
        }
    })
}
(jQuery));