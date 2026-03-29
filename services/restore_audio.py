import states
from sklearn.ensemble import RandomForestClassifier
from services.audio_compressor import convert_to_pcm, bytes_to_halftone

#for the random forest to work I will need the corrupted audio positions, the corrupted audio and the reference audio

#first get the position of the corrupted audio bytes

def get_corrupted_audio(original_audio, corrupted_audio):

    corrupted_indexes = []
    shorter_arry = min(len(original_audio), len(corrupted_audio))

    for i in range(shorter_arry):
        if original_audio[i] != corrupted_audio[i]:
            corrupted_indexes.append(i)

    return corrupted_indexes

def get_surronding_values(audio_bytes, index):
    ##get the surronding bits of the corrupted audio
    ##This is done as audio is not random and surronding bits have pattens within eachother
    number_of_bits = 8
    surronding_bits = []

    for i in range(-number_of_bits, number_of_bits + 1):
        surronding_bit = index + i
        if 0 <= surronding_bit < len(audio_bytes):
            surronding_bits.append(float(audio_bytes[surronding_bit]))
        else:
            surronding_bits.append(0.0)

    halftone_index = index // 4
    for i in range(-number_of_bits, number_of_bits + 1):
        surronding_bit = halftone_index + i
        if 0 <= surronding_bit < len(audio_bytes):
            surronding_bits.append(float(audio_bytes[surronding_bit]))
        else:
            surronding_bits.append(0.0)

    surronding_bits.append(float(index))
    return surronding_bits

def train_random_forest(corrupted_audio, reference_audio, original_audio, corrupted_indexes):
    x_train = []
    y_train = []

    corrupted_set = set(corrupted_indexes)
    shorter_array = min(len(original_audio), len(corrupted_audio))


    for i in range(shorter_array):
        if i not in corrupted_set:
            surronding_bits = get_surronding_values(reference_audio, i)
            x_train.append(surronding_bits)
            y_train.append(int(original_audio[i]))

    classifier = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    classifier.fit(x_train, y_train)

    return classifier

def restore_audio(corrupted_pcm, halftone_samples, corrupted_indexes, classifier):
    restored_audio = list(corrupted_pcm)

    x_predict = []
    for i in corrupted_indexes:
        surronding_bits = get_surronding_values(corrupted_pcm, halftone_samples, i)
        x_predict.append(surronding_bits)

    predictions = classifier.predict(x_predict)
    probabilities = classifier.predict_proba(x_predict)

    confidence_threshhold = 0.9

    for index, value_prediction, prob in zip(corrupted_indexes, predictions, probabilities):
        if max(prob) >= confidence_threshhold:
            restored_audio[index] = int(value_prediction)

    return restored_audio

def run_random_forest(corrupted_audio, reference_audio, original_audio):

    corrupted_indexes = get_corrupted_audio(original_audio, corrupted_audio)

    classifier = train_random_forest(corrupted_audio, reference_audio, original_audio, corrupted_indexes)

    restored_audio = restore_audio(corrupted_audio, reference_audio, corrupted_indexes, classifier)

    states.audio_metrics.update({
        'rf_restored_indexes': len(corrupted_indexes),
    })

    return restored_audio