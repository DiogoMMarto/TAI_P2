package pt.ua.tai.meta;

import java.util.*;
import java.util.logging.Logger;

public class Meta {
    private final Logger log = Logger.getLogger(getClass().getName());
    private final Map<String, CharCounts> frequencyTable = new HashMap<>();
    private final Set<Character> alphabet = new LinkedHashSet<>();
    private final int k;
    private final String content;

    public Meta(String content, int k) {
        this.content = content;
        this.k = k;
        init();
    }
    
    public void init() {
        generateAlphabetSet();
        generateFrequencyTable(k);
    }

    public List<String> getBestSequences(Map<String, String> db, float alpha, int n) {
        return batchRun(db, alpha).entrySet().stream()
                .sorted(Map.Entry.comparingByValue(Comparator.reverseOrder()))
                .limit(n)
                .map(Map.Entry::getKey)
                .toList();
    }

    public Map<String, Double> batchRun(Map<String, String> db, float alpha) {
        Map<String, Double> results = new HashMap<>();
        db.entrySet().parallelStream().forEach(it ->
                results.put(it.getKey(), estimateTotalBits(it.getValue(), alpha))
        );
        return results;
    }

    public double estimateTotalBits(String sequence, float alpha) {
        final float alphaTimesAlphabet = alpha * alphabet.size();
        double totalSum = 0.0F;

        StringBuilder contextBuilder = new StringBuilder(sequence.substring(0, k));
        final int sequenceLength = sequence.length();

        for (int i = 0; i + k < sequenceLength; i++) {
            final String context = contextBuilder.toString();
            final char nextChar = sequence.charAt(i + k);
            CharCounts charCounts = frequencyTable.getOrDefault(context, new CharCounts());
            float symbolBits = getSymbolBits(charCounts, nextChar, alpha, alphaTimesAlphabet);
            totalSum += symbolBits;
            if (i + k + 1 < sequenceLength) {
                contextBuilder.deleteCharAt(0).append(sequence.charAt(i + k));
            }
        }
        return totalSum / Math.log(2);
    }

    private float getSymbolBits(CharCounts charCounts, char nextChar, float alpha, float alphaTimesAlphabet) {
        final int contextTotalCount = charCounts.getTotalCount();
        final float denominator = contextTotalCount + alphaTimesAlphabet;
        final float probability = (charCounts.get(nextChar) + alpha) / denominator;
        return (float) Math.log(probability);
    }

    /**
     * Creates the context and succeeding character and count Map
     *
     * @param k context width
     */
    private void generateFrequencyTable(int k) {
        final int contentLength = content.length();
        StringBuilder contextBuilder = new StringBuilder(content.substring(0, k));
        for (int i = 0; i + k < content.length(); i++) {
            final String context = contextBuilder.toString();
            final char nextChar = content.charAt(i + k);
            CharCounts charCounts = frequencyTable.computeIfAbsent(context, key -> new CharCounts());
            charCounts.increment(nextChar);
            if (i + k + 1 < contentLength) {
                contextBuilder.deleteCharAt(0).append(content.charAt(i + k));
            }
        }
    }

    /**
     * Generate an alphabet from the symbols used in the content
     */
    private void generateAlphabetSet() {
        for (int i = 0; i < content.length(); i++) {
            alphabet.add(content.charAt(i));
        }
    }

}
