package com.agri.backend.service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.bson.Document;
import org.bson.types.ObjectId;
import org.springframework.stereotype.Component;

@Component
public class MongoDocumentMapper {
    public Map<String, Object> toMap(Document document) {
        Map<String, Object> result = new LinkedHashMap<>();
        document.forEach((key, value) -> {
            String targetKey = "_id".equals(key) ? "id" : key;
            result.put(targetKey, convert(value));
        });
        return result;
    }

    public List<Map<String, Object>> toMaps(Iterable<Document> documents) {
        List<Map<String, Object>> result = new ArrayList<>();
        for (Document document : documents) {
            result.add(toMap(document));
        }
        return result;
    }

    @SuppressWarnings("unchecked")
    private Object convert(Object value) {
        if (value instanceof ObjectId objectId) {
            return objectId.toHexString();
        }
        if (value instanceof Date date) {
            return date.toInstant().toString();
        }
        if (value instanceof LocalDateTime dateTime) {
            return dateTime.toString();
        }
        if (value instanceof Document document) {
            return toMap(document);
        }
        if (value instanceof Map<?, ?> map) {
            Map<String, Object> converted = new LinkedHashMap<>();
            map.forEach((key, item) -> converted.put(String.valueOf(key), convert(item)));
            return converted;
        }
        if (value instanceof List<?> list) {
            return list.stream().map(this::convert).toList();
        }
        return value;
    }
}