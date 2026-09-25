// Ported from a VBA module: Attribute VB_Name = "Legacy"
/* The old code was: Public Sub Run(ByVal x As Long) ... Dim y As Long */
public class LegacyPort {
    public static void run(Integer x) {
        Integer y = x;
    }
}
