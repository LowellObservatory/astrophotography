
# Usage: flats_norm.py date

# if "date" is not supplied, we can look for the most recent flat.

# Find all the flats in the database from the supplied date.
# Copy those flats to the work directory.
# For each filter:
#   For each set of flats in a given filter:
#     Subtract dark and bias from the flat
#       If we have an average dark with the same exposure, just subtract that.
#       Otherwise, use the average bias and the normalized dark * exposure.
#     Normalize by dividing by the average value
#   Median combine this set of flats with max clipping to remove stars.
#   Renormalize this final flat by dividing it by its mean
#
# Place the normalized flats in the "current_cal_files" directory
