public class PVCalculator {
    public static void main(String[] args) {
        if (args.length != 4) {
            System.err.println("Usage: java PVCalculator <irradiance> <temp> <efficiency> <area>");
            System.exit(1);
        }

        try {
            double irradiance = Double.parseDouble(args[0]);
            double temp = Double.parseDouble(args[1]);
            double efficiency = Double.parseDouble(args[2]);
            double area = Double.parseDouble(args[3]);

            double tempCoeff = 0.005;
            double loss = (temp - 25.0) * tempCoeff;
            double realEfficiency = efficiency * (1.0 - loss);
            double powerWatts = irradiance * area * realEfficiency;
            double powerKw = Math.max(0.0, powerWatts / 1000.0);

            System.out.println(powerKw);
            System.out.println(loss);
        } catch (NumberFormatException e) {
            System.err.println("All parameters must be numeric.");
            System.exit(2);
        }
    }
}
