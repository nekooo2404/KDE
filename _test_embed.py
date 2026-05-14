import django, os, time
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tweet_locator.settings')
django.setup()

from location_app.utils.world_city_dataset import WorldCityDataset
from location_app.utils.embedding_location import build_embedding_index, predict_location_by_similarity, _index

print('Loading WorldCityDataset...')
t0 = time.time()
ds = WorldCityDataset()
print(f'  Dataset: {ds.total_cities:,} cities ({time.time()-t0:.2f}s)')

print('Building TF-IDF index...')
t1 = time.time()
build_embedding_index(ds)
print(f'  Index: {_index.index_size:,} cities indexed ({time.time()-t1:.2f}s)')

tests = [
    'Dao bo qua Marina Bay roi ghe Merlion truoc khi tiep tuc xuong Orchard Road',
    'Watching sunset at Eiffel Tower in Paris, absolutely breathtaking',
    'Morning coffee in Shibuya crossing, Tokyo never sleeps',
    'Ha Noi buoi sang, pho co dong nguoi',
    'Sydney Opera House is incredible, Bondi Beach tomorrow',
    'Lost in Hanoi old quarter, bun bo for breakfast',
]

print()
for tweet in tests:
    t2 = time.time()
    try:
        result = predict_location_by_similarity(tweet, ds)
        city = result['predicted_city']
        score = result['confidence']
        elapsed = time.time() - t2
        print(f'  [{city}] score={score:.3f} ({elapsed:.3f}s)')
        print(f'    Tweet: {tweet[:70]}')
    except Exception as e:
        print(f'  ERROR: {e}')
    print()
