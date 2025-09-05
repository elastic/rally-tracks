## Behavioral Analytcis Track

This track is for benchmarking behavioral analytics event ingestion.

The dataset contains ~25M events randomly generated.

To generate the JSON dataset run this command:

```bash
python3 _tools/event_generator.py > documents.json
````

### Example Documents

```json
{"event_type": "page_view", "payload": {"session": {"id": "9e148f81-746f-4a09-8818-8c2812284da6"}, "user": {"id": "d0206d74-7cdf-4a34-8925-6c672555fc8c"}, "page": {"url": "http://elastic.co/f6bb638a-c3e3-493c-b288-4cdd11be46b0?82655ac8-fb8b-4de7-a75b-f786399b0431", "title": "4287c28a-e312-4222-b094-2c997fc1e403", "referrer": "http://elastic.co/a7c6fb92-ffa3-4aba-963f-daea3c10367d?abbb253e-3757-42c9-803c-d8e5b1805365"}, "document": {"id": "491248f8-b15e-4221-933a-9af752710184", "index": "index-2d"}}}
```


```json
{"event_type": "search", "payload": {"session": {"id": "9e148f81-746f-4a09-8818-8c2812284da6"}, "user": {"id": "d0206d74-7cdf-4a34-8925-6c672555fc8c"}, "search": {"query": "4ee62034-275e-4ef0-9d2f-2d8fad0d92e9", "search_application": "index-1d", "page": {"current": 78, "size": 50}, "sort": {"name": "relevance", "direction": "desc"}, "results": {"total_results": 8863, "items": [{"page": {"url": "http://elastic.co/6160062a-b7d9-40f3-b44d-f803707bc327?df17e5ea-dbe4-42c2-b77d-d3ef8060eb8e"}, "document": {"id": "96570382-359c-48c7-8bd7-cb3ffbdfc3a8", "index": "index-1d"}}, {"page": {"url": "http://elastic.co/94711df7-f592-4398-a493-911ff68856d0?85982040-8d0f-468f-bacf-cdfe71af4da4"}, "document": {"id": "9e6a5d69-a3f3-4576-af54-3b473b61b2b9", "index": "index-1d"}}, {"page": {"url": "http://elastic.co/9e193944-6d69-4c71-a439-4f319b56b6f8?de211b26-11a5-4c90-bc78-56aae20a6330"}, "document": {"id": "0d168994-2795-4167-b2e8-f970c58467a0", "index": "index-2d"}}, {"page": {"url": "http://elastic.co/1967cb79-7300-462d-8788-05ab7548bd6a?3862e1e7-7925-4e45-9200-1fce4c056132"}, "document": {"id": "7fcc3fc1-876a-44c0-acb9-9ea443c824c8", "index": "index-2d"}}, {"page": {"url": "http://elastic.co/50592d77-b3f4-4f32-b6b7-31a5266e47c2?70ed0ab6-a28c-4388-b5b6-f4ed520462d3"}, "document": {"id": "86b415e5-0450-421b-a2bc-c3f42cc74898", "index": "index-1d"}}, {"page": {"url": "http://elastic.co/1d4b487a-ea95-4160-a8fd-e1782b63169b?626502c6-222e-4e4d-87ce-dbd649d70922"}, "document": {"id": "a9547e91-29b7-4f13-b234-8db6e0e161cd", "index": "index-1d"}}, {"page": {"url": "http://elastic.co/d3882040-7bbf-46ca-86d6-96dde61d1d1f?9a77af05-2f01-4848-ac36-fbcfe3ea684b"}, "document": {"id": "5603497e-f082-4eaf-9b79-90b078d7daeb", "index": "index-1d"}}, {"page": {"url": "http://elastic.co/368500fa-b4f9-4e71-bc43-d106ba7c6f50?34a624a4-63b7-47cb-9751-e75edf5abdb2"}, "document": {"id": "8ec05a68-05c0-49ea-9957-c36b46b8df96", "index": "index-2d"}}, {"page": {"url": "http://elastic.co/b24a1b1a-8535-41bf-ac35-8ec7f8ca11d6?aa3409f5-8a7a-42ac-a841-f5084e996efe"}, "document": {"id": "69897531-3aef-46d7-b279-409b1e5dcd5e", "index": "index-2d"}}, {"page": {"url": "http://elastic.co/7c74f14f-fbbc-425f-b0e5-8bcc18f0469c?690849b8-7723-4e3e-bc05-ad060891b041"}, "document": {"id": "353f6706-9991-4750-b8e5-4c09bf8679c8", "index": "index-1d"}}]}}}}
```

### Parameters

This track accepts the following parameters with Rally 0.8.0+ using `--track-params`:

* `target_throughput` (default: 2000): Number of events per seconds submitted by the clients.
* `ingest_clients` (default: 1): Number of clients that issue event post requests.
