import pdb
import matplotlib as M
M.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as N

from defaults import Defaults
from figure import Figure
import WEM.utils.utils as utils
import scales

class BirdsEye(Figure):
    def __init__(self,config,wrfout):
        self.C = config
        self.W = wrfout
        self.D = Defaults()
        self.p2p = self.C.output_root
        print self.p2p

    def plot_data(self,data,mplcommand,fpath,pt,V=0):
        """
        Generic method that plots any matrix of data on a map

        Inputs:
        data        :   lat/lon matrix of data
        m           :   basemap instance
        mplcommand  :   contour or contourf
        fpath       :   absolute filepath including name
        V           :   scale for contours

        """
        # INITIALISE
        self.fig = plt.figure()
        self.fig = self.figsize(8,8,self.fig)     # Create a default figure size if not set by user
        self.bmap,x,y = self.basemap_setup()

        if mplcommand == 'contour':
            if not V:
                self.bmap.contour(x,y,data)
            else:
                self.bmap.contour(x,y,data,V)
        elif mplcommand == 'contourf':
            if not V:
                self.bmap.contourf(x,y,data,alpha=0.5)
            else:
                self.bmap.contourf(x,y,data,V,alpha=0.5)



        # LABELS, TITLES etc
        """
        Change these to hasattr!
        """
        #if self.C.plot_titles:
        title = utils.string_from_time('title',pt,tupleformat=0)
        plt.title(title)
        #if self.C.plot_colorbar:
        plt.colorbar(orientation='horizontal')

        # SAVE FIGURE
        datestr = utils.string_from_time('output',pt,tupleformat=0)
        self.fname = self.create_fname(fpath) # No da variable here
        self.save(self.fig,self.p2p,self.fname)
        self.fig.clf()

    def plot2D(self,va,vardict,da=0,na=0):
        """
        Inputs:

        va      :   variable

        vardict     :   dictionary of
            pt  :   plot time
            lv  :   level
            vc  :   vertical coordinate system

        Other arguments:

        da      : dictionary of:
            tla     :   top limit of latitude
            bla     :   bottom limit of latitude
            llo     :   left limit of longitude
            rlo     :   right limit of longitude


        """
        # INITIALISE
        #en = self.W.path
        self.fig = plt.figure()
        self.fig = self.figsize(8,8,self.fig)     # Create a default figure size if not set by user
        self.bmap,x,y = self.basemap_setup()

        # Unpack dictionary
        lv = vardict['lv']
        pt = vardict['pt']
        # pdb.set_trace()

        # Get indices for time, level, lats, lons
        # TIME
        if pt == 'all':
            time_idx = slice(None,None)
        elif pt == 'range':
            start_frame = self.W.get_time_idx(vardict['itime'], tuple_format=1)
            end_frame = self.W.get_time_idx(vardict['ftime'], tuple_format=1)
            time_idx = slice(start_frame,end_frame)
        else:
            time_idx = self.W.get_time_idx(pt)

        # LAT/LON
        lat_sl, lon_sl = self.get_limited_domain(da)

        # LEVEL
        vc = vardict['vc']
        if vc == 'surface':
            lv_idx = 0
        elif lv == 'all':
            lv_idx = 'all'
        else:
            print("Need to sort other levels")
            raise Exception

        lv_na = utils.get_level_naming(va,**vardict)

        """
           def plot_strongest_wind(self,dic):
                itime = dic['itime']
                ftime = dic['ftime']
                V = dic.get('range',(10,32.5,2.5))
                F = BirdsEye(self.C,W

        """

        # Now clear dictionary of old settings
        # They will be replaced with indices
        # vardict.pop('pt')
        # vardict.pop('lv')
        # try:
            # vardict.pop('da')
        # except KeyError:
            # pass

        # FETCH DATA
        PS = {'t': time_idx, 'lv': lv_idx, 'la': lat_sl, 'lo': lon_sl}
        data = self.W.get(va,PS,**vardict)

        la_n = data.shape[-2]
        lo_n = data.shape[-1]

        # COLORBAR, CONTOURING
        cm, clvs = scales.get_cm(va,**vardict)
        # Override contour levels if specified
        # clvs = vardict.get('range',clvs_default)

        # pdb.set_trace()
        if cm:
            self.bmap.contourf(x,y,data.reshape((la_n,lo_n)),clvs,cmap=cm)
        elif isinstance(clvs,N.ndarray):
            self.bmap.contourf(x,y,data.reshape((la_n,lo_n)),clvs,cmap=plt.cm.jet)
        # elif isinstance(clvs,tuple) or isinstance(clvs,list):
            # N.array(clvs)
            # self.bmap.contourf(x,y,data.reshape((la_n,lo_n)),clvs,cmap=plt.cm.jet)
        else:
            self.bmap.contourf(x,y,data.reshape((la_n,lo_n)))

        # LABELS, TITLES etc
        if self.C.plot_titles:
            title = utils.string_from_time('title',pt,**vardict)
            plt.title(title)
        if self.C.colorbar:
            plt.colorbar(orientation='horizontal')

        # SAVE FIGURE
        datestr = utils.string_from_time('output',pt)
        if not na:
            # Use default naming scheme
            na = (va,lv_na,datestr)
        else:
            # Come up with scheme...
            print("Coming soon: ability to create custom filenames")
            raise Exception
        self.fname = self.create_fname(*na) # No da variable here
        self.save(self.fig,self.p2p,self.fname)
        plt.close()

    def basemap_setup(self):
        # Fetch settings
        basemap_res = getattr(self.C,'basemap_res',self.D.basemap_res)

        width_m = self.W.dx*(self.W.x_dim-1)
        height_m = self.W.dy*(self.W.y_dim-1)

        m = Basemap(
            projection='lcc',width=width_m,height=height_m,
            lon_0=self.W.cen_lon,lat_0=self.W.cen_lat,lat_1=self.W.truelat1,
            lat_2=self.W.truelat2,resolution=basemap_res,area_thresh=500
            )
        m.drawcoastlines()
        m.drawstates()
        m.drawcountries()

        # Draw meridians etc with wrff.lat/lon spacing
        # Default should be a tenth of width of plot, rounded to sig fig

        x,y = m(self.W.lons,self.W.lats)
        return m, x, y


