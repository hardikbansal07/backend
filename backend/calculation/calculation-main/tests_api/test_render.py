import pytest
from api import render as renderer


class SimplePlanet:
    def __init__(self, name, absoluteLongitude=None, rawLongitudeDeg=None, houseAbs=None):
        self.name = name
        self.absoluteLongitude = absoluteLongitude
        self.rawLongitudeDeg = rawLongitudeDeg
        self.houseAbs = houseAbs


class SimpleChart:
    def __init__(self, planets=None, ascendantSignNumber=1):
        self.planets = planets or []
        self.ascendantSignNumber = ascendantSignNumber


def test_chart_to_positions_basic():
    planets = [SimplePlanet('Sun', absoluteLongitude=100.0), SimplePlanet('Moon', absoluteLongitude=220.0)]
    chart = SimpleChart(planets=planets, ascendantSignNumber=1)
    pos = renderer.chart_to_positions(chart, size=200)
    assert isinstance(pos, dict)
    assert 'planets' in pos and 'houses' in pos
    assert len(pos['planets']) == 2
    assert len(pos['houses']) == 12
    # planet coordinates should be inside the image bounds
    for p in pos['planets']:
        assert 0.0 <= p['x'] <= 200.0
        assert 0.0 <= p['y'] <= 200.0


def test_render_chart_svg_south_and_north():
    planets = [SimplePlanet('Mars', absoluteLongitude=10.0), SimplePlanet('Venus', absoluteLongitude=300.0)]
    chart = SimpleChart(planets=planets, ascendantSignNumber=1)
    svg_south = renderer.render_chart_svg(chart, style='South', theme='Light', size=300)
    assert isinstance(svg_south, str)
    assert svg_south.strip().startswith('<svg')
    assert '<circle' in svg_south

    svg_north = renderer.render_chart_svg(chart, style='North', theme='Light', size=300)
    assert isinstance(svg_north, str)
    assert svg_north.strip().startswith('<svg')
    # North-style should contain rect boxes for houses
    assert '<rect' in svg_north


def test_render_empty_planets():
    chart = SimpleChart(planets=[], ascendantSignNumber=1)
    svg = renderer.render_chart_svg(chart, style='South', theme='Light', size=200)
    assert svg.startswith('<svg')
    # still should contain house labels
    assert '1' in svg
