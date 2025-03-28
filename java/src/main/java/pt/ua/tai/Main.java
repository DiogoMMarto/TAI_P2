package pt.ua.tai;

import pt.ua.tai.meta.Meta;

import java.util.List;
import java.util.Map;

import static pt.ua.tai.database.DatabaseReader.readFileAndCreateDbMap;
import static pt.ua.tai.database.DatabaseReader.readTxtFileToString;

public class Main {

    public static void main(String[] args) {
        try {
            Map<String, String> dbMap = readFileAndCreateDbMap("sequences/db.txt");
            String metaContent = readTxtFileToString("sequences/meta.txt");
            Meta meta = new Meta(metaContent, 2);
            List<String> best = meta.getBestSequences(dbMap, 0.1f, 20);
            best.forEach(x -> System.out.println(x));
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}