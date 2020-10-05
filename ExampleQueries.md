# Example Queries

## Before you begin

- load the data by simply opening up the [UI](http://localhost:5000)
- go the the Search UI in [RedisInsight](http://localhost:8001/instance/b3268041-9940-43e3-b375-0857a8d1ce08/redisearch/)

## Searches

### Get Everything
```
*
```

### Search everywhere for the term computer

```
Computer
```


### Find all technology companies not in California or NewYork

```
"@sector:Technology -@hqstate:(CA|NY)"
```

### Fuzzy Match the CEO

```
@ceo:%dill%
```

### Exact Match the CEO

```
@ceo:"Sean M. Connolly"
```

### Prefix match the company name

```
@title:Wal*
```



## Ordering

### Find me the top 5 companies posting losses in profits

```
"@profits:[-inf,0]" SORTBY profits ASC LIMIT 0 5
```

NOTE: field must be marked as Sortable


## Aggregations

Aggregation functions are available here: https://oss.redislabs.com/redisearch/Aggregations/#list_of_field_apply_functions

### Aggregate by State with a function

```
"*" APPLY "upper(@hqstate)" as state GROUPBY 1 @state REDUCE COUNT 0 AS my_count SORTBY 2 @my_count DESC
```


### Aggregate by State not NY or CA

```
"-@hqstate:(CA|NY)" GROUPBY 1 @hqstate REDUCE COUNT 0 AS my_count SORTBY 2 @my_count DESC
```

### Aggregate by State and Industry

```
"*" GROUPBY 2 @hqstate @industry REDUCE COUNT 0 AS my_count SORTBY 4 @my_count DESC @hqstate DESC
```

### Aggregate by Sector with sum of revenues

```
"*" GROUPBY 2 @sector @hqstate REDUCE SUM 1 @revenues SORTBY 4 @revenues DESC @hqstate DESC
```
