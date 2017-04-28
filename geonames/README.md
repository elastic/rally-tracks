## Geonames track

This track is based on a [geonames](http://www.geonames.org/) dump of the file [allCountries.zip](http://download.geonames.org/export/dump/allCountries.zip) retrieved as of April 27, 2017. 

For further details about the semantics of individual fields, please see the [geonames dump README](http://download.geonames.org/export/dump/readme.txt).

Modifications:

* The original CSV data have been converted to JSON.
* We combine the original `longitude` and `latitude` fields to a new `location` field of type [geo_point](https://www.elastic.co/guide/en/elasticsearch/reference/current/geo-point.html).

### License

We use the same license for the data as the original data from Geonames:

```
This work is licensed under a Creative Commons Attribution 3.0 License,
see http://creativecommons.org/licenses/by/3.0/
The Data is provided "as is" without warranty or any representation of accuracy, timeliness or completeness.
```