from asgiref.sync import sync_to_async

@sync_to_async
def create_record(model, **fields):
    return model.objects.create(**fields)