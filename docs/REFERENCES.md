# Research references

- Jan Lukas Storck (2024), [Automation of crochet technology and development of a prototype machine for the production of complex-shaped textiles](https://www.hsbi.de/publikationsserver/record/4792). Reference for mechanical stitch registration, support handling and crochet motion sequences.
- Bergou, Wardetzky, Robinson, Audoly and Grinspun (2008), [Discrete Elastic Rods](https://www.cs.columbia.edu/cg/rods/). Reference for numerical rod mechanics.
- [CadQuery](https://cadquery.readthedocs.io/): parametric solid modeling tool used by this project.
- [K&S Precision Metals](https://ksmetals.com/pages/material-specifications): stock material dimensions.
- [Polymaker technical data](https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/pla/polylite-tm-pla): typical polymer properties.

References credit prior work and explain the design's technical context.
Third-party papers and source CAD are not redistributed here.

- Kaldor, James and Marschner(2008), [Simulating Knitted Cloth at the Yarn Level](https://www.cs.cornell.edu/projects/YarnCloth/): yarn-level geometry, length conservation and contact modeling.

- [Numba compilation documentation](https://numba.readthedocs.io/en/stable/user/jit.html): compilation and caching used for the exact line/arc contact kernel.

- Hanna, Singh and Virga(2018), [Partial constraint singularities in elastic rods](https://arxiv.org/abs/1711.00900): force, moment and energy balances at a material-throughflow boundary, with planar inextensible sleeve examples.

- Kaldor, James and Marschner(2010), [Efficient Yarn-based Cloth with Adaptive Contact Linearization](https://research.cs.cornell.edu/YarnCloth/): yarn contact modeling context. Its adaptive linearization is not implemented here.
- [Abaqus contact enforcement documentation](https://docs.software.vt.edu/abaqusv2026/English/SIMACAEITNRefMap/simaitn-c-contactconstraints.htm): numerical penalty enforcement and compliance; this project uses its own solver.

- Dauphin et al.(2014), [Identifying and attacking the saddle point problem in high-dimensional non-convex optimization](https://proceedings.neurips.cc/paper_files/paper/2014/hash/04192426585542c54b96ba14445be996-Abstract.html): section6 motivates the absolute-eigenvalue search metric; its experiments concern optimization, not textile hardware.
