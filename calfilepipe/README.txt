
This module produces a set of "reduced calibration images" from a set of
calibration images taken on particular day.  These calibration images
consist of:

1. N bias images (where N >= 1)
2, N x E dark images (where E is Exposure time, and N is number of dark images
                      using that exposure time.  N >= 1 for each E.)
3. N x F flat images (where F is Filter, and N is number of flat images in
                      that filter. N >= 1 for each F.)

This module will produce:

1. An average bias image: the average of the N bias images.
2. Average dark images: one for each exposure time, average of N darks at
   each exposure time. (bias not subtracted)
3. A average normalized dark: the average of all "long exposure darks" after
   they have been normalized by dividing each by its exposure time after
   subtracting the average bias.
4. Nomalized flats in each filter: for each filter, dark/bias subtract each
   of N flats, then, normalize by dividing by the average value.  Finally the
   N flats in this filter are median combined with max clipping to get
   rid of stars. Divide this final flat by its mean to renormalize.
