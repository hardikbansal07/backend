import inspect, sys, os
print('CWD', os.getcwd())
print('sys.path[0]', sys.path[0])
try:
    import api.app as ap
    print('Imported api.app from', inspect.getfile(ap))
    for r in ap.app.router.routes:
        p = getattr(r,'path',None); m=getattr(r,'methods',None)
        if p: print('ROUTE', p, m)
except Exception as e:
    print('Initial import error:', e)
if 'src' not in sys.path:
    sys.path.insert(0,'src')
try:
    import api.app as ap2
    print('Re-imported api.app from', inspect.getfile(ap2))
    for r in ap2.app.router.routes:
        p = getattr(r,'path',None); m=getattr(r,'methods',None)
        if p: print('ROUTE2', p, m)
except Exception as e:
    print('Post-add src import error:', e)
