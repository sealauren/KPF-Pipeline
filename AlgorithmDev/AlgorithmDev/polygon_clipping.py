"""This module does polygon clipping on simulated spectral order trace described in fits style"""

from __future__ import print_function
from astropy.io import fits
from astropy.utils.data import get_pkg_data_filename
import math
import numpy as np
import copy
import csv
from numpy.polynomial.polynomial import polyval, polyder
from numpy import sqrt, square

X = 0
Y = 1
C0 = 0
C1 = 1
C2 = 2
C3 = 3

class PolygonClipping:
    """Class for doing polygon clipping on simulated spectral trace.

    Parameters:
        fits_file (str): path for fits_file which contains the fitting polynomial coefficient for the spectral trace.

    """


    def __init__(self, fits_file=None, order_width=5):
        self.spectral_curve_file = fits_file
        self.order_width = order_width


    def load_paras_spectral(self, filename=None):
        """Load paras spectral trace from the fits file"""
        header_key_map = {
            'NAXIS1': 'xdim',
            'NAXIS2': 'ydim',
        }
        fits_name = self.spectral_curve_file if filename is None else filename
        if fits_name is None:
            return None

        fits_header = fits.open(fits_name)
        if len(fits_header) < 1:
            return None

        spectral_info = {'data': fits_header[0].data}
        header = fits_header[0].header
        header_keys = list(header.keys())
        for k in header_keys:
            if k in header_key_map.keys():
                spectral_info[header_key_map.get(k)] = int(header[k])
 
        return spectral_info

    def load_csv_file(self, filename, delimit=','):
        rows = []
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=delimit)
            for row in csv_reader:
                row_num = [float(n) for n in row]
                rows.append(row_num)

        return rows

    def load_simple_spectral_info(self):
        """Load simple spectral trace from the fits file"""
        header_key_map = {
            'NAXIS1': 'xdim',
            'NAXIS2': 'ydim',
        }
        COEFF = 'COEFF'

        if self.spectral_curve_file is None:
            return None

        fits_header = fits.open(self.spectral_curve_file)
        if len(fits_header) < 1:
            return None


        spectral_info = {'data': fits_header[0].data}
        header = fits_header[0].header
        header_keys = list(header.keys())

        coeffs = []
        n_idx = len(COEFF)

        for k in header_keys:
            if k in header_key_map.keys():
                spectral_info[header_key_map.get(k)] = int(header[k])
            elif k.startswith(COEFF):
                coeffs.insert(int(k[n_idx:]), header[k])

        spectral_info.update({'coeffs': coeffs})

        return spectral_info


    def rectify_spectral_curve(self, coeffs, in_data, s_rate=[1, 1], sum_extraction=True, verbose=False):
        """Straighten the spectral trace

        Parameters:
            coeffs (list): polynomial coefficient list starting from that of zero order
            in_data (array): input data
            s_rate (list): sampling rate from input domain to output domain
            sum_extraction(bool): flag to indicate if performing summation on rectified curve or not
            verbose(bool): flag for debug


        Returns:
            spectral_info (dict): straightened spectral information including dimension and the data

        """

        s = np.shape(in_data)
        input_xdim = s[1]
        input_ydim = s[0]
        sampling_rate = []
        if type(s_rate).__name__ == 'list':
            sampling_rate.extend(s_rate)
        else:
            sampling_rate.append([s_rate, s_rate])

        output_xdim = input_xdim * sampling_rate[X]
        output_ydim = input_ydim * sampling_rate[Y]

        if verbose is True:
            print('output_xdim: ', output_xdim, 'sampling_rate: ', sampling_rate)

        # construct corners map between input and output
        y_mid = []                                              # spectral trace value at mid point
        x_step = []                                             # x step in input domain
        y_norm_step = []                                        # curve norm along x in input domain
        x_output_step = list(range(0, output_xdim+1))           # x step in output domain, both ends are included

        #if verbose is True:
        #   print('x_output_step=', x_output_step)

        for o_x in x_output_step:
            crt_x = self.get_input_pos(o_x, sampling_rate[X])
            x_step.insert(o_x, crt_x)
            y_mid.insert(o_x, polyval(crt_x, coeffs))
            y_norm_step.insert(o_x, self.poly_normal(crt_x, coeffs, sampling_rate[Y]))

        v_border = [max(y_mid), min(y_mid)]
        if verbose is True:
            print('v_border: ', v_border)

        # the vertical position to locate the output spectral
        v_mid = self.get_output_pos(math.floor((v_border[0]+v_border[1])/2), sampling_rate[Y])
        if verbose is True:
            print('v_mid: ', v_mid)

        input_upper_corners = []   # corners above the curve, row based list
        input_lower_corners = []   # corners below the curve, row based list

        output_width = int(self.get_input_pos(self.order_width, sampling_rate[Y]))  # width of output
        upper_width = min(output_width, output_ydim - v_mid)
        lower_width = min(output_width, v_mid)
        if verbose is True:
            print('width at output: ', upper_width, lower_width)

        corners_at_mid = [[x, y] for x, y in zip(x_step, y_mid)]
        #if verbose is True:
        #   print('corners_at_mid: ', corners_at_mid)

        y_size = 1 if sum_extraction is True else (upper_width+lower_width)
        out_data = np.zeros((y_size, output_xdim))

        input_upper_corners.insert(0, corners_at_mid.copy())
        input_lower_corners.insert(0, corners_at_mid.copy())

        for o_y in range(1, upper_width+1):
            next_upper_corners = [self.go_vertical(input_upper_corners[o_y-1][o_x], y_norm_step[o_x], 1) for
                                        o_x in x_output_step]
            input_upper_corners.insert(o_y, next_upper_corners)

        for o_y in range(1, lower_width+1):
            next_lower_corners = [self.go_vertical(input_lower_corners[o_y-1][o_x], y_norm_step[o_x], -1) for
                                        o_x in x_output_step]
            input_lower_corners.insert(o_y, next_lower_corners)

        for o_x in x_output_step[0:-1]:
            for o_y in range(0, upper_width):
                input_corners = [input_upper_corners[o_y+c[0]][o_x+c[1]] for c in [[0, 0], [1, 0], [1, 1], [0, 1]]]
                flux = self.compute_output_flux(input_corners, in_data, input_xdim, input_ydim, False)
                if sum_extraction is True:
                    out_data[0, o_x] += flux
                    #if verbose is True:
                    #    print(o_y, o_x, flux, out_data[0, o_x])
                else:
                    out_data[lower_width+o_y, o_x] = flux

            for o_y in range(0, lower_width):
                input_corners = [input_lower_corners[o_y+c[0]][o_x+c[1]] for c in [[1, 0], [0, 0], [0, 1], [1, 1]]]
                flux = self.compute_output_flux(input_corners, in_data, input_xdim, input_ydim, False)
                if sum_extraction is True:
                    out_data[0, o_x] += flux
                    #if verbose is True:
                    #    print(o_y, o_x, flux, out_data[0, o_x])
                else:
                    out_data[lower_width-o_y-1, o_x] = flux

            if verbose is True:
                print('[%d %.2f]' % (o_x, out_data[0, o_x]), end=' ')

        if verbose is True:
            print(' ')
        result_data = {'y_center': v_mid,
                       'width': [upper_width, lower_width],
                       'dim': [output_ydim, output_xdim],
                       'out_data': out_data}

        return result_data

    def rectify_spectral_curve_by_optimal(self, coeffs, in_data, flat_data, s_rate=[1, 1], verbose=False):
        s_result = self.rectify_spectral_curve(coeffs, in_data, s_rate, sum_extraction=False)
        f_result = self.rectify_spectral_curve(coeffs, flat_data, s_rate, sum_extraction=False)

        height = sum(s_result.get('width'))
        width = s_result.get('dim')[1]
        w_data = np.zeros((1, width))

        s_data = s_result.get('out_data')
        f_data = f_result.get('out_data')

        for x in range(0, width):
            w_sum = sum(f_data[:, x])
            w_data_tmp = [ s_data[y, x] * f_data[y, x]/w_sum for y in range(0, height)]
            w_data[0, x] = sum([ s_data[y, x] * f_data[y, x]/w_sum for y in range(0, height)])

        result_data = {'y_center': s_result.get('y_center'),
                       'dim': s_result.get('dim'),
                       'out_data': w_data
                       }

        return result_data


    def rectify_spectral_curve_by_sum(self, coeffs, in_data, s_rate=[1,1], verbose=False):
        """Straighten the spectral trace and perform the summation on the rectify trace

        Parameters:
            coeffs (list): polynomial coefficient list starting from that of zero order
            in_data (array): input data
            s_rate (list): sampling rate from input domain to output domain
            verbose(bool): flag for debug


        Returns:
            spectral_info (dict): straightened spectral information including dimension and the data

        """

        result_data = self.rectify_spectral_curve(coeffs, in_data, s_rate, True, verbose)
        if verbose is True:
            print('rectify curve: ', result_data)

        return self.sum_curve(result_data.get('out_data'), verbose)


    def sum_curve(self, flat_data, verbose=False):
        """Sum a band of spectral trace

        Parameters:
            flat_data(array): flatten trace
            verbose(bool): flag for debug

        Returns:
            out_data(array): sum extraction of one rectified flat

        """

        sum_data = np.sum(flat_data, axis=0)
        if verbose is True:
            print('sum curve: ', sum_data)

        s = np.shape(sum_data)
        out_data = np.zeros((1, s[0]))
        for x in range(0, s[0]):
            out_data[0, x] = sum_data[x]
        return out_data

    def fill_2D_to_2D(self, from_data, to_data, from_center, to_center):
        """Fill a band of 2D data into another band of 2D from one vertical position to another one

        Parameters:
            from_data(array): data to be copied from
            to_data(array): 2D area to copy the data to
            from_center(number): locate the center of the from_data
            to_center(number): to the center of the to_data

        """

        s = np.shape(from_data)
        from_xdim = s[1]
        from_ydim = s[0]

        center_dist = to_center - from_center;
        for x in range(0, from_xdim):
            for y in range(0, from_ydim):
                to_data[center_dist+y, x] = from_data[y, x]

    def poly_normal(self, pos_x, coeffs, sampling_rate = 1):
        """ Calculate the normal at the specified x position per vertical sampling rate"""

        d_coeff = polyder(coeffs)
        tan = polyval(pos_x, d_coeff)
        v_norm = [-tan, 1]/(sampling_rate * sqrt(tan*tan+1))
        return v_norm

    def get_input_pos(self, output_pos, s_rate):
        """ Get associated position at input domain per output position and sampling rate"""

        return output_pos/s_rate

    def get_output_pos(self, input_pos, s_rate):
        """ get the associated output position per input position and sampling rate"""

        return math.floor(input_pos*s_rate)     # position at output cell domain is integer based

    def go_vertical(self, pos, norm, direction = 1):
        """ Get positions of next row along the normal direction at each position"""

        new_pos = [ p + direction*n for p, n in zip(pos, norm)]
        return new_pos

    def is_zero_coverage(self, corners, input_data):
        """ Check if all corners are located at zero valued cells"""

        s = np.shape(input_data) # 0: y dim, 1: x dim
        s_x = s[1] - 1
        s_y = s[0] - 1
        corners_on_cell = [[max(0, min(math.floor(c[X]), s_x)),
                            max(0, min(math.floor(c[Y]), s_y))] for c in corners]
        non_zero_corners = [ c for c in corners_on_cell if input_data[c[Y], c[X]] != 0.0]
        return len(non_zero_corners) == 0

    def is_out_range(self, corners, input_data):
        """ Check if all corners are located out of a domain"""

        size = np.shape(input_data)
        corners_on_cell = [[math.floor(c[X]), math.floor(c[Y])] for c in corners]
        return all([(c[Y] < 0 or c[Y] > size[0] or c[X] < 0 or c[X] > size[1]) for c in corners_on_cell])


    def compute_output_flux(self, input_corners, input_data, input_xdim, input_ydim, verbose=False):
        """ compute the flux per corners and a matrix of data per polygon clipping algorithm

        Parameters:
            input_corners(list): corners at input domain
            input_data(array): input data
            input_xdim(number): width of input data
            input_ydim(number): height of input data
            verbose(bool): flag for debug

        Returns:
            flux(number): flux value

        """
        if verbose is True:
            print('input_corners: ', input_corners)

        x_list = [input_corners[i][X] for i in range(0, 4)]
        y_list = [input_corners[i][Y] for i in range(0, 4)]
        x_1 = min(x_list)
        x_2 = max(x_list)
        y_1 = min(y_list)
        y_2 = max(y_list)

        y_1 = max(0, math.floor(y_1))
        y_2 = min(input_ydim, math.ceil(y_2))
        x_1 = max(0, math.floor(x_1))
        x_2 = min(input_xdim, math.ceil(x_2))

        if verbose is True:
            print('x_1:', x_1, ' x2:', x_2, ' y1:', y_1, ' y2:', y_2)

        flux = 0.0
        for x in range(x_1, x_2):
            for y in range(y_1, y_2):
                if verbose is True:
                    print('input_data[', y, x,']: ', input_data[y, x])

                if input_data[y, x] != 0.0:
                    new_corners = self.polygon_clipping(input_corners, [[x, y], [x, y+1], [x+1, y+1], [x+1, y]], 4)
                    area = self.polygon_area(new_corners)
                    if verbose is True:
                        print('area: ', area)
                    flux += area * input_data[y, x]

        return flux

    def polygon_clipping(self, poly_points, clipper_points, clipper_size):
        """ New polygon points after performing the clipping based on the specified clipping area"""

        new_poly_points = copy.deepcopy(poly_points)

        for i in range(clipper_size):
            k = (i+1)%clipper_size
            new_poly_points = self.clip(new_poly_points, clipper_points[i][0], clipper_points[i][1],
                                   clipper_points[k][0], clipper_points[k][1])

        return self.remove_duplicate_point(new_poly_points)

    def remove_duplicate_point(self, corners):
        """ Remove the duplicate points from a list of corner points"""

        new_corners = []
        for c in corners:
            if c not in new_corners:
                new_corners.append(c)

        return new_corners

    def polygon_area(self, corners):
        """ Calculate the polygon area per polygon corners"""

        polygon_size = len(corners)
        area = 0.0
        for i in range(polygon_size):
            k = (i+1)%polygon_size
            area += corners[i][0]*corners[k][1] - corners[k][0]*corners[i][1]

        return abs(area)/2


    def clip(self, poly_points, x1, y1, x2, y2):
        """ Polygon clipping"""

        new_points = []
        poly_size = len(poly_points)

        for i in range(poly_size):
            k = (i+1)%poly_size
            ix = poly_points[i][0]
            iy = poly_points[i][1]
            kx = poly_points[k][0]
            ky = poly_points[k][1]

            # position of first point w.r.t. clipper line
            i_pos = (x2 - x1) * (iy - y1) - (y2 - y1) * (ix - x1)
            # position of second point w.r.t. clipper line
            k_pos = (x2 - x1) * (ky - y1) - (y2 - y1) * (kx - x1)

            if i_pos < 0 and k_pos < 0:             # both are inside, take the second
                new_points.append([kx, ky])
            elif i_pos >= 0 and k_pos < 0:          # only the second is inside, take the intersect and the second one
                if i_pos == 0:
                    new_points.append([ix, iy])
                else:
                    intersect_p = self.line_intersect(x1, y1, x2, y2, ix, iy, kx, ky)
                    new_points.append([intersect_p[0], intersect_p[1]])
                new_points.append([kx, ky])
            elif i_pos < 0 and k_pos >= 0:          # onlyt the first inside,  take the intersect
                if k_pos == 0:
                    new_points.append([kx, ky])
                else:
                    intersect_p = self.line_intersect(x1, y1, x2, y2, ix, iy, kx, ky)
                    new_points.append([intersect_p[0], intersect_p[1]])

        return new_points


    def line_intersect(self, x1, y1, x2, y2, x3, y3, x4, y4):
        den = (x1-x2)*(y3-y4) - (x3-x4)*(y1-y2)
        num_x = (x1*y2 - x2*y1) * (x3 - x4) - (x1 - x2) * (x3*y4 - x4*y3)
        num_y = (x1*y2 - x2*y1) * (y3 - y4) - (y1 - y2) * (x3*y4 - x4*y3)
        return [num_x/den, num_y/den]

    def get_vertical_width(self, data_array, x, y):
        """Computer vertical width up and down between [x, y[0]] and [x+1, y[1]]"""

        array_size = np.shape(data_array)
        y_top = array_size[0]
        y_start = math.floor(min(y))

        # vertical width stop at windth_top and width_bottom
        s_to_top = y_top - 1 - y_start
        s_to_bottom = y_start

        for i in range(y_start, y_top, 1):
            if data_array[i, x] == 0.0:
                s_to_top = i - y_start
                break
        for i in range(y_start - 1, 0, -1):
            if data_array[i, x] == 0.0:
                s_to_bottom = y_start - i
                break

        return [s_to_top, s_to_bottom]

    def get_spectral_vertical_range(self, xdim, ydim, data_array):
        """Find the spectral vertical coverage.

        Parameters:
            xdim (int): dimension along x axis
            ydim (int): dimension along y axis
            data: spectral data in 2D array

        Returns:
            vertical_range (list): vertical coverage range

        """

        y_range = np.nonzero(data_array)[0]
        r_len = len(y_range)

        return [y_range[0], y_range[r_len-1]] if r_len > 0 else None

              
