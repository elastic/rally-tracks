# EventData Data Set

This data set contains 20 million Apache access log entries generated based on sample 
elastic.co access logs using the generator avilable here: https://github.com/elastic/rally-eventdata-track

The size of the data file is around 15GB, which gives an average JSON record size of 822 bytes. mappings have been somewhat optimized and the _all field has been disabled.

The purpose of this track is to provide an efficient way to benchmark indexing of this data type as the generator
built into the rally-eventdata-track can be CPU intensive.

## License

We use the same license for the data as the original data from Geonames:

```
This work is licensed under a Creative Commons Attribution 4.0 License,
see https://creativecommons.org/licenses/by-sa/4.0/
The Data is provided "as is" without warranty or any representation of accuracy, timeliness or completeness.
```