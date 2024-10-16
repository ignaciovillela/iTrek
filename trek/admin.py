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
            puntos_js = [
                {
                    "lat": punto.latitud,
                    "lng": punto.longitud,
                    "descripcion": punto.interes.descripcion if hasattr(punto, 'interes') else None,
                    "imagen": punto.interes.imagen.url if hasattr(punto, 'interes') and punto.interes.imagen else None
                }
                for punto in obj.puntos.all()
            ]
            puntos_js_str = str(puntos_js).replace("None", "null").replace("'", '"')  # Convertir a JSON válido y manejar None

            form.base_fields['descripcion'].help_text = mark_safe(f"""
            <div id="mapid" style="height: 400px;"></div>
            <script>
                var map = L.map('mapid').setView([{obj.puntos.first().latitud}, {obj.puntos.first().longitud}], 13);
                
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    maxZoom: 18,
                    attribution: 'Map data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }}).addTo(map);
            
                var points = {puntos_js_str};
            
                var latlngs = [];
                points.forEach(function(p) {{
                    latlngs.push([p.lat, p.lng]);
            
                    var popupContent = "";
                    if (p.descripcion) {{
                        popupContent += "<b>Descripción:</b> " + p.descripcion;
                    }}
                    if (p.imagen) {{
                        if (popupContent !== "") {{
                            popupContent += "<br>";
                        }}
                        popupContent += '<img src="' + p.imagen + '" alt="Imagen del punto" style="max-width: 200px; max-height: 150px;">';
                    }}
            
                    if (popupContent !== "") {{
                        var marker = L.marker([p.lat, p.lng]).addTo(map);
                        marker.bindPopup(popupContent);
                    }}
                }});
            
                if (latlngs.length > 1) {{
                    var polyline = L.polyline(latlngs, {{color: 'blue'}}).addTo(map);
                    map.fitBounds(polyline.getBounds());
                }} else if (latlngs.length === 1) {{
                    map.setView(latlngs[0], 13);
                }}
            </script>
            """)
        return form

admin.site.register(Ruta, RutaAdmin)
