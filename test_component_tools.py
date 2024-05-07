import unittest
from tools.component_tools import Component, Fluid, Membrane, FluidMaterial
from io import StringIO
from unittest.mock import patch


class TestMSComponent(unittest.TestCase):
    def setUp(self):
        # Create a Component object with some initial values
        fluid = Fluid(
            T=300,
            D=1e-9,
            Solubility=0.5,
            MS=True,
            mu=1e-3,
            rho=1000,
            k=0.5,
            cp=1.0,
            k_t=0.1,
            U0=0.2,
            d_Hyd=0.3,
        )
        membrane = Membrane(k_d=1e7, D=0.4, thick=0.5, K_S=0.6, T=300, k_r=1e7, k=0.8)
        self.component = Component(c_in=0.5, eff=0.8, fluid=fluid, membrane=membrane)

    def test_outlet_c_comp(self):
        # Test the outlet_c_comp() method
        self.component.outlet_c_comp()
        self.assertAlmostEqual(self.component.c_out, 0.1)

    def test_T_leak(self):
        # Test the T_leak() method
        leak = self.component.T_leak()
        self.assertAlmostEqual(leak, 0.4)

    def test_get_regime(self):
        self.component2 = Component(c_in=0.5, eff=0.8)
        regime = self.component2.get_regime()
        self.assertEqual(regime, "No fluid selected")
        self.component2.fluid = Fluid(k_t=0.1, Solubility=0.2, MS=True)
        # Test the get_regime() method
        regime = self.component2.get_regime()
        self.assertEqual(regime, "No membrane selected")
        self.component2.membrane = Membrane(
            k_d=1e7, D=0.4, thick=0.5, K_S=0.6, T=300, k_r=1e7, k=0.8
        )
        regime = self.component2.get_regime()
        self.assertEqual(regime, "Mixed regime")

    def test_get_adimensionals(self):
        # Test the get_adimensionals() method

        self.component.get_adimensionals()
        self.assertEqual(self.component.H, 200000000)
        self.assertEqual(self.component.W, 41666666.66666667)

    def test_use_analytical_efficiency(self):
        # Test the use_analytical_efficiency() method
        self.component.use_analytical_efficiency(L=1.0)
        self.assertAlmostEqual(self.component.eff, 0.99871669093034)

    def test_get_efficiency(self):
        # Test the get_efficiency() method
        self.component.get_efficiency(L=1.0)

        self.assertAlmostEqual(self.component.eff, 0.998984924629, places=2)

    def test_analytical_efficiency(self):
        # Test the analytical_efficiency() method
        self.component.analytical_efficiency(L=1.0)
        self.assertAlmostEqual(self.component.eff_an, 0.9987166909303, places=2)

    def test_get_flux(self):
        # Test the get_flux() method
        flux = self.component.get_flux(c=0.3)
        self.assertAlmostEqual(flux, 0.0015, places=2)

    def test_get_global_HX_coeff(self):
        # Test the get_global_HX_coeff() method
        U = self.component.get_global_HX_coeff(R_conv_sec=0.1)
        self.assertAlmostEqual(self.component.U, 2.9215784663, places=4)

    def test_efficiency_vs_analytical(self):
        # Test the efficiency_vs_analytical() method
        self.component.analytical_efficiency(L=1.0)
        self.component.get_efficiency(L=1.0, c_guess=self.component.c_in / 2)
        self.assertAlmostEqual(
            abs(self.component.eff - self.component.eff_an) / self.component.eff_an,
            0,
            places=2,
        )

    def test_inspect(self):
        result = "c_in: 0.5\neff: 0.8\nfluid is a <class 'tools.component_tools.Fluid'> class, printing its variables:\n    T: 300\n    Solubility: 0.5\n    MS: True\n    D: 1e-09\n    k_t: 0.1\n    d_Hyd: 0.3\n    mu: 0.001\n    rho: 1000\n    U0: 0.2\n    k: 0.5\n    cp: 1.0\nmembrane is a <class 'tools.component_tools.Membrane'> class, printing its variables:\n    T: 300\n    D: 0.4\n    thick: 0.5\n    k_d: 10000000.0\n    K_S: 0.6\n    k_r: 10000000.0\n    k: 0.8\nH: None\nW: None"
        expected_output = result
        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.component.inspect()
            self.assertEqual(fake_out.getvalue().strip(), expected_output.strip())


class TestLMComponent(unittest.TestCase):
    def setUp(self):
        # Create a Component object with some initial values
        fluid = Fluid(
            T=300,
            D=1e-9,
            Solubility=0.5,
            MS=False,
            mu=1e-3,
            rho=1000,
            k=0.5,
            cp=1.0,
            k_t=0.1,
            U0=0.2,
            d_Hyd=0.3,
        )
        membrane = Membrane(k_d=1e7, D=0.4, thick=0.5, K_S=0.6, T=300, k_r=1e7, k=0.8)
        self.component = Component(c_in=0.5, eff=0.8, fluid=fluid, membrane=membrane)

    def test_outlet_c_comp(self):
        # Test the outlet_c_comp() method
        self.component.outlet_c_comp()
        self.assertAlmostEqual(self.component.c_out, 0.1)

    def test_T_leak(self):
        # Test the T_leak() method
        leak = self.component.T_leak()
        self.assertAlmostEqual(leak, 0.4)

    def test_get_regime(self):
        self.component2 = Component(c_in=0.5, eff=0.8)
        regime = self.component2.get_regime()
        self.assertEqual(regime, "No fluid selected")
        self.component2.fluid = Fluid(k_t=0.1, Solubility=0.2, MS=True)
        # Test the get_regime() method
        regime = self.component2.get_regime()
        self.assertEqual(regime, "No membrane selected")
        self.component2.membrane = Membrane(
            k_d=1e7, D=0.4, thick=0.5, K_S=0.6, T=300, k_r=1e7, k=0.8
        )
        regime = self.component2.get_regime()
        self.assertEqual(regime, "Mixed regime")

    def test_get_adimensionals(self):
        # Test the get_adimensionals() method

        self.component.get_adimensionals()
        self.assertEqual(self.component.H, 72000000)
        self.assertEqual(self.component.W, 7500000)

    def test_use_analytical_efficiency(self):
        # Test the use_analytical_efficiency() method
        self.component.use_analytical_efficiency(L=1.0)
        self.assertAlmostEqual(self.component.eff, 0.998295638580)

    def test_get_efficiency(self):
        # Test the get_efficiency() method
        self.component.get_efficiency(L=1.0, c_guess=self.component.c_in / 2)

        self.assertAlmostEqual(self.component.eff, 0.998295638580, places=2)

    def test_analytical_efficiency(self):
        # Test the analytical_efficiency() method
        self.component.analytical_efficiency(L=1.0)
        self.assertAlmostEqual(self.component.eff_an, 0.998295638580, places=2)

    def test_get_flux(self):
        # Test the get_flux() method
        flux = self.component.get_flux(c=0.3)
        self.assertAlmostEqual(flux, 0.01314458525095, places=2)

    def test_get_global_HX_coeff(self):
        # Test the get_global_HX_coeff() method
        U = self.component.get_global_HX_coeff(R_conv_sec=0.1)
        self.assertAlmostEqual(self.component.U, 2.9215784663, places=4)

    def test_efficiency_vs_analytical(self):
        # Test the efficiency_vs_analytical() method
        self.component.analytical_efficiency(L=1.0)
        self.component.get_efficiency(L=1.0, c_guess=self.component.c_in / 2)
        self.assertAlmostEqual(
            abs(self.component.eff - self.component.eff_an) / self.component.eff_an,
            0,
            places=2,
        )

    def test_inspect(self):
        result = "c_in: 0.5\neff: 0.8\nfluid is a <class 'tools.component_tools.Fluid'> class, printing its variables:\n    T: 300\n    Solubility: 0.5\n    MS: False\n    D: 1e-09\n    k_t: 0.1\n    d_Hyd: 0.3\n    mu: 0.001\n    rho: 1000\n    U0: 0.2\n    k: 0.5\n    cp: 1.0\nmembrane is a <class 'tools.component_tools.Membrane'> class, printing its variables:\n    T: 300\n    D: 0.4\n    thick: 0.5\n    k_d: 10000000.0\n    K_S: 0.6\n    k_r: 10000000.0\n    k: 0.8\nH: None\nW: None"
        expected_output = result
        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.component.inspect()
            self.assertEqual(fake_out.getvalue().strip(), expected_output.strip())


class TestFluidMaterial(unittest.TestCase):
    def setUp(self):
        self.fluid_material = FluidMaterial(
            T=300, D=1e-9, Solubility=0.5, MS=True, mu=1e-3, rho=1000, k=0.5, cp=1.0
        )

    def test_attributes(self):
        self.assertEqual(self.fluid_material.T, 300)
        self.assertEqual(self.fluid_material.D, 1e-9)
        self.assertEqual(self.fluid_material.Solubility, 0.5)
        self.assertEqual(self.fluid_material.MS, True)
        self.assertEqual(self.fluid_material.mu, 1e-3)
        self.assertEqual(self.fluid_material.rho, 1000)
        self.assertEqual(self.fluid_material.k, 0.5)
        self.assertEqual(self.fluid_material.cp, 1.0)

        # def test_inspect(self):
        #     result = "c_in: 0.5\neff: 0.8\nfluid is a <class 'tools.component_tools.Fluid'> class, printing its variables:\n    T: 300\n    Solubility: 0.5\n    MS: True\n    D: 1e-09\n    k_t: 0.1\n    d_Hyd: 0.3\n    mu: 0.001\n    rho: 1000\n    U0: 0.2\n    k: 0.5\n    cp: 1.0\nmembrane is a <class 'tools.component_tools.Membrane'> class, printing its variables:\n    T: 300\n    D: 0.4\n    thick: 0.5\n    k_d: 10000000.0\n    K_S: 0.6\n    k_r: 10000000.0\n    k: 0.8\nH: None\nW: None"
        #     expected_output = result

        # with patch("sys.stdout", new=StringIO()) as fake_out:
        #     self.component.inspect()
        #     self.assertEqual(fake_out.getvalue().strip(), expected_output.strip())


if __name__ == "__main__":
    unittest.main()
