public with sharing class GreetingService {
    private String name;

    public GreetingService(String name) {
        this.name = name;
    }

    public String greet() {
        return format(name);
    }

    private static String format(String value) {
        return 'Hello ' + value;
    }
}
