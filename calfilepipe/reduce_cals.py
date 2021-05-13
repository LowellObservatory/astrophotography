import bias_ave
import darks_ave
import norm_darks
import flats_norm

bias_ave.bias_ave(directory)
darks_ave.darks_ave(directory)
norm_dark.norm_dark(directory)
flats_norm.flats_norm(directory)

if __name__ = "__main__":
  if (len(sys.argv) != 2):
    print("usage: reduce_cals directory")
    return

  directory = sys.argv[0]
  bias_ave.bias_ave(directory)
  darks_ave.darks_ave(directory)
  norm_dark.norm_dark(directory)
  flats_norm.flats_norm(directory)

