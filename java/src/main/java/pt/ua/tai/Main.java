package pt.ua.tai;

import picocli.CommandLine.Option;
import pt.ua.tai.meta.Meta;

import java.util.Map;

import static pt.ua.tai.database.DatabaseReader.readFileAndCreateDbMap;
import static pt.ua.tai.database.DatabaseReader.readTxtFileToString;

public class Main {
    @Option(names = {"-f", "--file"}, description = "File name", required = true)
    private String fileName;
    @Option(names = {"-v", "--verbose"}, description = "Verbose output", defaultValue = "false")
    private boolean verbose;
    @Option(names = {"-a", "--alpha"}, description = "Smoothing parameter alpha")
    private Float alpha;
    @Option(names = {"-k", "--contextWidth"}, description = "Context width")
    private Integer k;

    public static void main(String[] args) {
        try {
            Map<String, String> dbMap = readFileAndCreateDbMap("sequences/db.txt");
            String metaContent = readTxtFileToString("sequences/meta.txt");
            Meta meta = new Meta(metaContent, 13);
            Map<String, Double> best = meta.getBestSequences(dbMap, 1f, 20);

            best.entrySet().stream().sorted(Map.Entry.comparingByValue())
                    .forEach(e -> System.out.println(e.getValue() + "\t" + e.getKey()));
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}