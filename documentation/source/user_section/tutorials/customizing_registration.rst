.. _customizing-registration-section:

Customizing the ``sct_register_to_template`` command
####################################################

This page provides recommendations for how to adjust ``sct_register_to_template`` when the default parameters aren't sufficient for your specific data and pipeline.

Because choosing the right configuration for your data can be overwhelming, feel free to visit the `SCT forum <https://forum.spinalcordmri.org/c/sct/>`_ where you can ask for clarification and guidance.

The ``-param`` argument
***********************

The ``-param`` argument controls which transformations are applied at each step of the registration process. ``-param`` provides many configurations to choose from; this makes it powerful and flexible, but also challenging to work with.

The easiest way to approach ``-param`` is to begin with the default command, then make small adjustments one parameter at a time. The default values for ``-param`` are shown below:

.. code-block::

   # Note: Command has been split up for readability. Normally, you would input this with no line breaks.
   -param step=0,type=label,dof=Tx_Ty_Tz_Sz:
          step=1,type=imseg,algo=centermassrot,metric=MeanSquares,iter=10,smooth=0,gradStep=0.5,slicewise=0,smoothWarpXY=2,pca_eigenratio_th=1.6:
          step=2,type=seg,algo=bsplinesyn,metric=MeanSquares,iter=3,smooth=1,gradStep=0.5,slicewise=0,smoothWarpXY=2,pca_eigenratio_th=1.6

This long string of values defines a 3-step transformation. Each step is separated by a `:` character, and each step begins with ``"step=#"``. The parameters for each step are separated by `,` characters.

Typically, step 0 is not altered. However, steps 1 and 2 can be tweaked, and additional steps (e.g. 3, 4) can be added.

These default parameters have been chosen so that step 1 applies coarse adjustments, while step 2 applies fine adjustments. In general, we recommend that you stick to this kind of approach, by gradually applying finer and finer adjustments with each successive step.

   .. figure:: https://raw.githubusercontent.com/spinalcordtoolbox/doc-figures/master/registration_to_template/sct_register_to_template-param-algo.png
      :align: right
      :figwidth: 40%

      Visualization of algorithms to choose from for the ``algo`` parameter of ``-param``.

* ``algo`` This is the algorithm used to compute the nonrigid deformation. Choice of algorithm depends on how coarse/fine you want your transformation to be. This depends on which step you are modifying (Step 1, step 2, step 3, etc.) as well as the nature of the spinal cord you are working with.

   - **translation**: axial translation (x-y)
   - **rigid**: x-y translation + rotation about z axis
   - **affine**:
   - **b-splinesyn**: based on ants binaries
   - **syn**: (not bspline regularized)
   - **slicereg**: slice-wise translations (x-y). The translations within each slice are regularized across slices in the superior-inferior (S-I) direction. This algorithm can be used to align two images that are already "close" to each other, or it can be used to align two segmentations for a pre-alignment of cord centerline.
   - **centermassrot**: Compute the center of mass of the source and destination segmentation and align them slice-by-slice. This algorithm also estimates the orientation of the cord in the axial plane and matches that of the destination cord. This feature could be useful in case the subject rotated their neck, or if the cord is rotated due to a disc compression. Note that this algorithm only works with segmentations (contrary to slicereg).
   - **columnwise**: This algorithm is particularly interested in case of highly compressed cords. The first step consists in matching the edges of the source and destination segmentations in the R-L direction (scaling operation), and during the second step, each row of the source segmentation is matched to the destination segmentation (scaling operation in the A-P direction). After iterating across all rows in the R-L direction, a warping field is produced. This non-linear deformation is more controlled than the SyN-based approach. This method only works with segmentations (not images). The idea came from Dr. Allan Martin (University of Toronto, UC Davis).

* ``type``: Carefully choose ``type={im, seg}`` based on the quality of your data, and the similarity with the template. Ideally, you would always choose ``type=im``. However, if you find that there are artifacts of image features (e.g., no CSF/cord contrast) that could compromise the registration, then use ``type=seg`` instead. Of course, if you choose ``type=seg``, make sure your segmentation is good (manually adjust it if it is not). By default, ``sct_register_to_template`` relies on the segmentations only because it was found to be more robust to the existing variety of MRIs.
* ``metric``: Adjust metric based on type. With ``type=im``, use ``metric=CC`` (cross-correlation: accurate but long) or ``MI`` (mutual information: fast, but requires enough voxels). With ``type=seg`` or with images with the exact same contrast and intensity (e.g., fMRI time series, or two images acquired with the same acquisition parameters), use ``metric=MeanSquares``.
* ``slicewise``: Only applies to ``algo={translation, rigid, affine, syn, bsplinesyn}``. If set to `0`, a unique 3D transformation is estimated. If set to `1`, transformations are estimated for each axial slice independently.

The ``-ref`` argument
*********************

The flag ``-ref`` lets you select the destination for registration: either the template (default) or the subject’s native space. The main difference is that when ``-ref template`` is selected,
the cord is straightened, whereas with ``-ref subject``, it is not.

When should you use ``-ref subject``? If your image is acquired axially with highly anisotropic resolution (e.g. 0.7x0.7x5mm), the straightening will produce through-plane interpolation errors. In that case, it is better to register the template to the subject space to avoid such inaccuracies.

The ``-ldisc`` argument
***********************

The approach described previously uses two labels at the mid-vertebral level to register the template, which is fine if you are only interested in a relatively small region (e.g. C2 —> C7). However, if your volume spans a large superior-inferior length (e.g., C2 —> L1), the linear scaling between your subject and the template might produce inaccurate vertebral level matching between C2 and L1. In that case, you might prefer to rely on all inter-vertebral discs for a more accurate registration.

Conversely, if you have a very small FOV (e.g., covering only C3/C4), you can create a unique label at disc C3/C4 (value=4) and use -ldisc for registration. In that case, a single translation (no scaling) will be performed between the template and the subject.

.. note::
   If more than 2 labels are provided, ``-ldisc`` is not compatible with ``-ref subject``. For more information, please see the help: sct_register_to_template -h