import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

// Example output from scubber:
/* 
===== SCRUBBED SOURCE =====
import java.sql.DriverManager;



public class CLASS_TOKEN_001 {

    private String dbPassword = "CREDENTIAL_TOKEN_001";
    private String jdbcUrl = "CREDENTIAL_TOKEN_004";
    private String awsKey = "CREDENTIAL_TOKEN_002";
    private String supportPhone = "PII_PHONE_TOKEN_001";
    private String adminSsn = "PII_SSN_TOKEN_001";
    private String apiToken = "CREDENTIAL_TOKEN_003";

    public void processPayment(int amount) {
        
        String conn = DriverManager.getConnection("CREDENTIAL_TOKEN_005", "admin", "CREDENTIAL_TOKEN_006");
        System.out.println("Processing for PII_EMAIL_TOKEN_001");
    }
}


===== TOKEN MAP =====
{
  "CREDENTIAL_TOKEN_001": "super_secret_123",
  "CREDENTIAL_TOKEN_002": "AKIAIOSFODNN7EXAMPLE",
  "CREDENTIAL_TOKEN_003": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U",
  "CREDENTIAL_TOKEN_004": "jdbc:mysql://prod-db.internal:3306/payments",
  "CREDENTIAL_TOKEN_005": "jdbc:mysql://192.168.1.100/payments",
  "CREDENTIAL_TOKEN_006": "db_secret_456",
  "PII_EMAIL_TOKEN_001": "john.doe@gs.com",
  "PII_PHONE_TOKEN_001": "555-867-5309",
  "PII_SSN_TOKEN_001": "123-45-6789",
  "CLASS_TOKEN_001": "GoldmanSachsPaymentProcessor"
}

===== SCRUB REPORT =====
{
  "class": "GoldmanSachsPaymentProcessor",
  "total_replacements": 10,
  "by_category": {
    "CREDENTIAL": 6,
    "PII_EMAIL": 1,
    "PII_PHONE": 1,
    "PII_SSN": 1,
    "CLASS": 1
  },
  "by_origin": {
    "CREDENTIAL": {
      "knowledge_graph": 4,
      "regex": 2
    },
    "PII_EMAIL": {
      "regex": 1
    },
    "PII_PHONE": {
      "knowledge_graph": 1
    },
    "PII_SSN": {
      "knowledge_graph": 1
    },
    "CLASS": {
      "knowledge_graph": 1
    }
  }
}
*/

// This class handles payments for GoldmanSachs clients
/* Internal use only — contact john.smith@goldmansachs.com for access */
public class GoldmanSachsPaymentProcessor {

    private String dbPassword = "super_secret_123";
    private String jdbcUrl = "jdbc:mysql://prod-db.internal:3306/payments";
    private String awsKey = "AKIAIOSFODNN7EXAMPLE";
    private String supportPhone = "555-867-5309";
    private String adminSsn = "123-45-6789";
    private String apiToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U";

    public void processPayment(int amount) throws SQLException {
        // Connect using legacy JDBC — see ticket GS-1042
        Connection conn = DriverManager.getConnection("jdbc:mysql://192.168.1.100/payments", "admin", "db_secret_456");
        System.out.println("Processing for john.doe@gs.com");
    }
}
