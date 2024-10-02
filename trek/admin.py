from django.contrib import admin
from .models import Ruta, Punto
from django.utils.safestring import mark_safe

class PuntoInline(admin.TabularInline):
    model = Punto
    extra = 1
    fields = ['latitud', 'longitud', 'orden']
    classes = ['collapse']

class RutaAdmin(admin.ModelAdmin):
    inlines = [PuntoInline]

    class Media:
        css = {
            'all': ('https://unpkg.com/leaflet@1.7.1/dist/leaflet.css',)
        }
        js = ('https://unpkg.com/leaflet@1.7.1/dist/leaflet.js',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields['descripcion'].help_text = mark_safe(f"""
            <div id="mapid" style="height: 400px;"></div>
            <script>
            var map = L.map('mapid').setView([{obj.puntos.first().latitud}, {obj.puntos.first().longitud}], 13);
            
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 18,
                attribution: 'Map data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }}).addTo(map);

            var points = {[
                {"lat": punto.latitud, "lng": punto.longitud} for punto in obj.puntos.all()
            ]};

            var latlngs = points.map(function(p) {{
                return [p.lat, p.lng];
            }});

            var polyline = L.polyline(latlngs, {{color: 'blue'}}).addTo(map);
            map.fitBounds(polyline.getBounds());
            </script>
            """)
        return form

admin.site.register(Ruta, RutaAdmin)
