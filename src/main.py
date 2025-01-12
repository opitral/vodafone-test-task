import datetime
from pathlib import Path
import folium
from folium.plugins import Fullscreen
from internal.geo_analyzer import GeoAnalyzer


def main():
    geojson_path = Path(__file__).parent.parent / "resources/geojson" / "UKR-ADM1_simplified.geojson"
    geo = GeoAnalyzer(geojson_path, 49.0139, 31.4859)

    map_ukraine = folium.Map(location=[geo.center_lat, geo.center_lon], zoom_start=6)

    folium.GeoJson(
        geo.geojson_file,
        name="Borders of Ukraine",
        style_function=lambda x: {
            "color": "blue",
            "weight": 2,
            "fillOpacity": 0.1,
        }
    ).add_to(map_ukraine)

    folium.Marker(
        location=[geo.center_lat, geo.center_lon],
        popup="Center of Ukraine",
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(map_ukraine)

    extreme_points = geo.get_extreme_points()
    for direction, coords in extreme_points.items():
        folium.Marker(
            location=[coords["lat"], coords["lon"]],
            popup=f"{direction.capitalize()} Point",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(map_ukraine)

    matching_grid, not_matching_grid = geo.generate_grid(50, True)
    folium.GeoJson(
            matching_grid,
            name="Mathing Grid",
            style_function=lambda x: {
                "color": "green",
                "weight": 0.5,
                "fillOpacity": 0.1,
            }
        ).add_to(map_ukraine)
    folium.GeoJson(
            not_matching_grid,
            name="Not Matching Grid",
            style_function=lambda x: {
                "color": "red",
                "weight": 0.5,
                "fillOpacity": 0.1,
            }
        ).add_to(map_ukraine)

    bounds = geo.bounds
    folium.Rectangle(
        bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
        color="yellow",
        fill=False
    ).add_to(map_ukraine)

    folium.LayerControl().add_to(map_ukraine)
    Fullscreen().add_to(map_ukraine)

    map_ukraine.save(Path(__file__).parent.parent / "resources/output" /
                     f"{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.html")


if __name__ == "__main__":
    main()
