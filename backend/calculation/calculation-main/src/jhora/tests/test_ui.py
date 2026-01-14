#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) Open Astro Technologies, USA.
# Modified by Sundar Sundaresan, USA. carnaticmusicguru2015@comcast.net
# Downloaded from https://github.com/naturalstupid/PyJHora

# This file is part of the "PyJHora" Python library
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os
import sys
import pytest

_skip_headless = bool(os.environ.get('CI') or os.environ.get('PYJHORA_SKIP_UI_TESTS') or (sys.platform != 'win32' and not os.environ.get('DISPLAY')))

@pytest.mark.skipif(_skip_headless, reason="Skipping UI test in headless environment")
def test_ui_smoke_chart_tabbed():
    """Lightweight smoke test: instantiate main tabbed chart widget and close without starting full event loop.
    Avoids blocking call to exec(); ensures import & construction succeed.
    """
    from PyQt6.QtWidgets import QApplication
    # Reuse existing instance if already created (pytest may import other Qt using modules)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    from jhora.ui.horo_chart_tabs import ChartTabbed
    w = None
    try:
        w = ChartTabbed()
        # Optionally show & process a single iteration if platform supports (not required)
        try:
            w.show()
            # process a couple of events to trigger lazy inits
            app.processEvents()
        except Exception:
            pass
        assert w is not None
    finally:
        if w is not None:
            try:
                w.close()
            except Exception:
                pass
