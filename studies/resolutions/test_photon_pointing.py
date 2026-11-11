"""Analytic geometry and response checks; no simulation events are processed."""
import unittest
import numpy as np
from photon_pointing import CalorimeterSurface, smear_direction, photon_impact_parameters


class PointingTests(unittest.TestCase):
    def setUp(self):
        self.geometry = CalorimeterSurface(2250, 2500, 2500 / np.sinh(3), 2250)

    def test_surfaces_and_hole(self):
        vectors = np.array([[1, 0, 0], [1, 0, 2], [1, 0, -2],
                            [0, 0, 1], [1, 0, np.sinh(3.01)], [0, 0, 0]])
        hits, regions = self.geometry.intersect_from_origin(vectors)
        np.testing.assert_array_equal(regions, [1, 2, 2, 0, 0, 0])
        np.testing.assert_allclose(hits[:3], [[2250, 0, 0], [1250, 0, 2500],
                                            [1250, 0, -2500]])

    def test_inner_edge_and_endcap_gap(self):
        _, region = self.geometry.intersect_from_origin([[1, 0, np.sinh(3)]])
        self.assertEqual(region[0], 2)
        geometry = CalorimeterSurface(2250, 2500, 250, 2000)
        _, region = geometry.intersect_from_origin([[2100, 0, 2500]])
        self.assertEqual(region[0], 0)

    def test_known_impact_and_zero_smearing(self):
        n = np.array([[1., 0, 0], [0, 0, 1.]])
        np.testing.assert_allclose(smear_direction(n, 0, np.ones((2, 2))), n)
        ip3d, ipxy = photon_impact_parameters([[2250, 3, 4]], [[1, 0, 0]], [0, 0, 0])
        np.testing.assert_allclose(ip3d, [5])
        np.testing.assert_allclose(ipxy, [3])

    def test_one_mrad_rotation(self):
        smeared = smear_direction([[1., 0, 0]], .001, [[1., 0]])
        np.testing.assert_allclose(np.linalg.norm(smeared, axis=1), [1])
        ip, _ = photon_impact_parameters([[2250, 0, 0]], smeared, [0, 0, 0])
        np.testing.assert_allclose(ip, [2250 * np.sin(.001)], rtol=1e-12)

    def test_displaced_photon_closure(self):
        # A photon travels along +x from (2,3,4) mm. The origin-based
        # reconstructed direction points at its ideal barrel impact point.
        vertex = np.array([[2., 3., 4.]])
        truth = np.array([[1., 0., 0.]])
        impact = np.array([[np.sqrt(2250.**2 - 3.**2), 3., 4.]])
        hit, region = self.geometry.intersect_from_origin(impact)
        np.testing.assert_array_equal(region, [1])
        np.testing.assert_allclose(hit, impact)
        reco_ip, _ = photon_impact_parameters(hit, impact, [0, 0, 0])
        np.testing.assert_allclose(reco_ip, [0], atol=1e-12)
        direction = smear_direction(truth, 0, [[.7, -.2]])
        measured = photon_impact_parameters(hit, direction, [0, 0, 0])
        expected = photon_impact_parameters(vertex, truth, [0, 0, 0])
        np.testing.assert_allclose(measured, expected, atol=1e-12)
        np.testing.assert_allclose(measured, [[5.], [3.]])


if __name__ == "__main__":
    unittest.main()
