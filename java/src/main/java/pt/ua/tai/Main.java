package pt.ua.tai;

import pt.ua.tai.meta.Meta;

import java.util.Map;

import static pt.ua.tai.database.DatabaseReader.readFileAndCreateDbMap;
import static pt.ua.tai.database.DatabaseReader.readTxtFileToString;

public class Main {

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