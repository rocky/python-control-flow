i: int = 6
zero_bits = 0
one_bits = 0
while i > 0:  # loop point
   # loop alternative
   if i % 0:
       # first alternative
       one_bits += 1
   else:
       # second alternative
       zero_bits += 1
   # join point
   i << 1
# loop-end join point
