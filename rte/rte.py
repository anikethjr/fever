import os
import codecs
import pickle
import json
import numpy as np
import os
import subprocess

# global variable definition
labelToString = {
    0: "SUPPORTS",
    1: 'REFUTES',
    2: 'NOT ENOUGH INFO'}


def createTestSet(claim, candidateEvidences):
    testSetFile = codecs.open("./testSet_rte.jsonl", mode="w", encoding="utf-8")

    for elem in candidateEvidences:
        json.dump({"hypothesis": claim, "premise": elem}, testSetFile)
        testSetFile.write("\n")

    testSetFile.close()


def getPredictions(claim, evidence, claim_id):
    # call allennlp predictions shell script
    subprocess.call(['./allennlp_predictions.sh'])

    predsFile = codecs.open("./predictions_rte_individual.json", mode="r", encoding="utf-8")
    saveFile = codecs.open("entailment_predictions/claim_" + str(claim_id) + ".json", mode="w+", encoding="utf-8")

    rtePreds = []

    predsContent = predsFile.readlines()
    for i in range(len(predsContent)):
        rtePreds.append(json.loads(predsContent[i]))
        rtePreds[i]['claim'] = claim
        rtePreds[i]['premise_source_doc_id'] = evidence[i]['id']
        rtePreds[i]['premise_source_doc_line_num'] = evidence[i]['line_num']
        rtePreds[i]['premise_source_doc_sentence'] = evidence[i]['sentence']
        saveFile.write(json.dumps(rtePreds[i], ensure_ascii=False) + "\n")

    saveFile.close()
    predsFile.close()

    # for each element returns a dictionary of the form: {"predictedLabel": A, "confidence": B}
    predictionsProbability = []

    for prediction in rtePreds:
        maxIndex = np.argmax(np.asarray(prediction["label_probs"]))
        predictionsProbability.append({"predictedLabel": maxIndex, "confidence": prediction["label_probs"][maxIndex]})

    return predictionsProbability


def determinePredictedLabel(preds):
    supportPredictions = [elemIndex for elemIndex in range(len(preds)) if preds[elemIndex]["predictedLabel"] == 0]
    contradictionPredictions = [elemIndex for elemIndex in range(len(preds)) if preds[elemIndex]["predictedLabel"] == 1]
    nonePredictions = [elemIndex for elemIndex in range(len(preds)) if preds[elemIndex]["predictedLabel"] == 2]

    # determine the number of predictions for each case
    # return the prediction for the most predicted label and corresponding evidences
    numberOfPredictionsPerLabel = np.asarray(
        [len(nonePredictions), len(supportPredictions), len(contradictionPredictions)])
    mostCommonPrediction = np.argmax(numberOfPredictionsPerLabel)

    if mostCommonPrediction == 1:
        return (0, supportPredictions)
    elif mostCommonPrediction == 2:
        return (1, contradictionPredictions)
    else:
        return (2, [])


def textual_entailment_evidence_retriever(claim, evidence, claim_id):
    os.chdir("rte")
    potential_evidence_sentences = []
    for sentence in evidence:
        potential_evidence_sentences.append(sentence['sentence'])

    createTestSet(claim, potential_evidence_sentences)
    preds = getPredictions(claim, evidence, claim_id)
    predictedLabel, evidencesIndexes = determinePredictedLabel(preds)

    os.chdir("..")
    return {"claim": claim, "label": labelToString[predictedLabel], "evidence": np.asarray(evidence)[evidencesIndexes]}


"""
#### test #####

claim= "Gil was born in Porto"
candidateEvidences= ["Gil lives in Porto", "Gil was born in 1993 in Paris", "This document indicates that Gil was not born in Portugal"]

print(textual_entailment_evidence_retriever(claim, candidateEvidences))
"""
