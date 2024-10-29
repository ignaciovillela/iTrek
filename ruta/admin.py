import json

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.safestring import mark_safe

from user.models import Usuario
from .models import Punto, Ruta, RutaCompartida


class RutaForm(forms.ModelForm):
    class Meta:
        model = Ruta
        fields = '__all__'

    # Definir el widget para el campo ManyToMany
    compartida_con = forms.ModelMultipleChoiceField(
        queryset=Usuario.objects.all(),
        required=False,
        widget=FilteredSelectMultiple('Usuarios', is_stacked=False)
    )

    class Media:
        css = {
            'all': ('admin/css/widgets.css',),
        }
        js = ('admin/js/vendor/jquery/jquery.js', 'admin/js/jquery.init.js', 'admin/js/actions.js')


class PuntoInline(admin.TabularInline):
    model = Punto
    extra = 0
    fields = ['latitud', 'longitud', 'descripcion', 'imagen']
    readonly_fields = ('descripcion', 'imagen')

    @staticmethod
    def descripcion(obj):
        return obj.interes.descripcion

    @staticmethod
    def imagen(obj):
        if obj and obj.interes and obj.interes.imagen:
            return mark_safe(f'<a href="{obj.interes.imagen.url}"><img src="{obj.interes.imagen.url}" width="100" height="100" /></a>')
        return 'No hay imagen'


class RutaAdmin(admin.ModelAdmin):
    inlines = [PuntoInline]
    form = RutaForm
    list_display = ('nombre', 'usuario', 'dificultad', 'creado_en')
    list_filter = ('dificultad', 'usuario')

    class Media:
        css = {
            'all': ('https://unpkg.com/leaflet@1.7.1/dist/leaflet.css',)
        }
        js = ('https://unpkg.com/leaflet@1.7.1/dist/leaflet.js',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.puntos.exists():
            puntos_js = [
                {
                    "lat": punto.latitud,
                    "lng": punto.longitud,
                    "descripcion": punto.interes.descripcion if hasattr(punto, 'interes') else None,
                    "imagen": punto.interes.imagen.url if hasattr(punto, 'interes') and punto.interes.imagen else None
                }
                for punto in obj.puntos.all()
            ]
            puntos_js_str = json.dumps(puntos_js)
            first_punto = obj.puntos.first()

            form.base_fields['descripcion'].help_text = mark_safe(f"""
            <div id="mapid" style="height: 400px;"></div>
            <script>
                var map = L.map('mapid').setView([{first_punto.latitud}, {first_punto.longitud}], 13);
                
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


class RutaCompartidaForm(forms.ModelForm):
    class Meta:
        model = RutaCompartida
        fields = '__all__'

    # En el formulario de RutaCompartida, podemos mostrar el campo ManyToMany como un campo de selección filtrada
    usuario = forms.ModelChoiceField(queryset=Usuario.objects.all())
    ruta = forms.ModelChoiceField(queryset=Ruta.objects.all())


@admin.register(RutaCompartida)
class RutaCompartidaAdmin(admin.ModelAdmin):
    form = RutaCompartidaForm
    list_display = ('ruta', 'usuario')  # Mostramos los campos principales en la lista de admin
    search_fields = ('ruta__nombre', 'usuario__username')  # Buscamos por el nombre de la ruta o el nombre del usuario
    list_filter = ('ruta', 'usuario')  # Filtros por ruta y usuario


admin.site.register(Ruta, RutaAdmin)
