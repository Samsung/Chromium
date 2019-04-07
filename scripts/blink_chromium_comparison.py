import urllib2
import pandas as pd
import numpy as np
import datetime
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# function dealing with the html table
# each line
def InterpretLine(line):

    # split by the beginning of the table
    elements = line.split('<td>')

    # elements[0]: '<tr>'
    modified = elements[1][:-5]  # remove trailing '</td>'
    module = elements[2][:-5]  # remove trailing '</td>'
    url = elements[3].split('\'')[1]  # split and get the part between quotes
    subject = elements[3].split('\'>')[1][:
                                          -9]  # split and remove trailing '</a'
    author = elements[4][:-11]  # remove trailing '</td></tr>\n'

    # return a dictionary for each line
    return {
        'Modified': modified,
        'Module': module,
        'URL': url,
        'Subject': subject,
        'Author': author
    }


# dealing with the entire page
def ConvertPage(dataurl, savefilename=None):

    # get the page source
    response = urllib2.urlopen(dataurl)
    # read lines
    html = response.readlines()

    # use dictionary to store the conterted line
    data_dict = {}
    # a list to keep the indices of bad lines
    errors = []
    for ii in range(len(html)):
        try:
            data_dict[ii] = InterpretLine(html[ii])
        except:
            errors.append(ii)

    # save the result in the pandas dataframe
    data = pd.DataFrame.from_dict(data_dict).T
    if not savefilename == None:
        data.to_csv(savefilename, index=False)
    return data


# a method to add a new column to the data
# indicating the number of contribution of the certain author/module/etc. before that timepoint
def CountContribution(piece_data, colname='Author'):

    # simply add a column since we already sliced by a certain
    n_rows = piece_data.shape[0]
    piece_data[colname + 'Counts'] = np.arange(n_rows, 0, -1)

    # and return
    return piece_data


# a integrated method to analyze and plot the contribution according to the query
def SpecifyContribution(data,
                        colname,
                        day_start=None,
                        day_end=None,
                        max_names=5,
                        plot=True,
                        saveplot=None):

    # copy the data to avoid in place modification
    data = data.copy()
    # np.datetime64 variables for date and time
    data['Modified'] = np.array(data['Modified'].values, dtype=np.datetime64)

    # setting the target time period
    if day_start is None:
        day_start = data['Modified'].values.min()
    day_start = day_start.astype('datetime64[D]')
    data['Days_since'] = (
        data['Modified'].values - day_start) / np.timedelta64(1, 'D')
    data = data[data['Days_since'] >= 0]
    if not day_end is None:
        day_end = day_end.astype('datetime64[D]')
        data = data[data['Modified'] <= day_end]
    else:
        day_end = np.datetime64(datetime.datetime.now()).astype('datetime64[D]')

    # data get sorted by date, thus count goes up with time
    data = data.sort_values('Days_since', ascending=False)
    data = data.groupby(colname).apply(
        lambda x: CountContribution(x, colname=colname))

    # get the largest contributors who will appear in our plot
    col_conts = sorted(
        Counter(data[colname].values).items(), key=lambda x: x[1], reverse=True)
    cols = [cont[0] for cont in col_conts]

    if plot or (not saveplot == None):

        # plot the figure, use line plot
        fig = plt.figure(figsize=(18, 10))
        ax = fig.add_subplot(111)
        #         box = ax.get_position()
        ax.set_position([0.05, 0.075, 0.9, 0.9])

        # plot each name as a line
        for name in cols[:max_names]:
            data_to_plot = data[data[colname] == name][[
                'Days_since', colname + 'Counts'
            ]].values
            ax.plot(
                np.concatenate((data_to_plot[:, 0], [0])),
                np.concatenate((data_to_plot[:, 1], [0])),
                label=name,
                linewidth=2)
        ax.grid(True)

        # add the legend
        ax.legend(loc='upper left', fontsize=20)

        # axis ticks and ticklabels
        xticks = [
            str(year) + month + day
            for year in np.arange(
                day_start.astype(object).year,
                day_end.astype(object).year + 1)
            for month in ['-01', '-04', '-07', '-10'] for day in ['-01']
        ]
        xticklabels = [
            month + ('\n' + str(year)) *
            int(month == 'Jan.' or (month == 'Apr.' and year == 2013))
            for year in np.arange(
                day_start.astype(object).year,
                day_end.astype(object).year + 1)
            for month in ['Jan.', '', '', '']
        ]

        # add those labels
        ax.tick_params(axis='both', labelsize=20)
        ax.set_xticks((np.array(xticks, dtype=np.datetime64) - day_start) /
                      np.timedelta64(1, 'D'))
        ax.set_xticklabels(xticklabels, ha='left')
        # set the range of x
        ax.set_xlim(xmin=0, xmax=(day_end - day_start) / np.timedelta64(1, 'D'))

        if not saveplot == None:
            plt.savefig(saveplot, dpi=100)
        if plot:
            plt.show()

    return cols[:max_names]


def SaveModuleDistribution(dataurl, saveimgname=None):
    data = ConvertPage(dataurl)
    #    data = data[np.logical_or(data['Module'] == 'blink', data['Module'] == 'chromium')]

    for i in data['Module']:
        data['Module'] = 'Chromium Commits'

    if saveimgname == None:
        saveimgname = filter(str.isdigit,
                             np.datetime_as_string(
                                 np.datetime64(
                                     datetime.datetime.now()))) + '.png'
    SpecifyContribution(
        data,
        'Module',
        day_start=np.datetime64('2013-04-01'),
        plot=False,
        saveplot=saveimgname)


if __name__ == '__main__':

    # the html file
    dataurl = 'file:commits.html'

    # the target place
    saveimgname = 'samsung_chromium_contributions.png'

    SaveModuleDistribution(dataurl, saveimgname)
