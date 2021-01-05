.. _registration-to-template:

Registration to template
########################

This tutorial demonstrates how to use SCT's command-line scripts to register an anatomical MRI scan to the PAM50 Template, then use the results of this registration to perform basic quantitative analysis. We recommend that you read through the :ref:`pam50` page before starting this tutorial, as it provides an overview of the template included with SCT, as well as context for why it is used.

.. important::

   This tutorial uses sample MRI images that must be retrieved beforehand. Please download and unzip `sct_course_london20.zip <https://osf.io/bze7v/?action=download>`_, then open up the unzipped folder in your terminal and verify its contents using ``ls``.

   .. code:: sh

      ls
      # Output:
      # multi_subject single_subject

   We will be using images from the ``single_subject/data`` directory, so navigate there and verify that it contains subdirectories for various MRI image contrasts using ``ls``.

   .. code:: sh

      cd single_subject/data
      ls
      # Output:
      # dmri  fmri  LICENSE.txt  mt  README.txt  t1  t2  t2s

   We will start with T2-weighted images, so navigate to the ``t2`` directory and verify that it contains a T2-weighted anatomical image called ``t2.nii.gz``.

   .. code:: sh

      cd t2
      ls
      # Output:
      # t2.nii.gz

   .. figure:: https://raw.githubusercontent.com/spinalcordtoolbox/doc-figures/master/spinalcord_segmentation/t2_image.png
      :align: center
      :figwidth: 300px

      t2.nii.gz

.. _segmentation-section:

Step 1: Segmenting the spinal cord
**********************************

.. figure:: https://raw.githubusercontent.com/spinalcordtoolbox/doc-figures/master/registration_to_template/registration-pipeline-1.png
   :align: center
   :figwidth: 75%

   Steps performed by ``sct_deepseg_sc``.

.. note::

   The :ref:`spinalcord-segmentation` tutorial provides a more in-depth look at spinal cord segmentation. If you have already completed that tutorial, your ``t2/`` directory should contain a file called ``t2_seg.nii.gz``. If it does, you may skip this section and proceed with the :ref:`vert-labeling-section` section.

Theory
======

First, we will run the ``sct_deepseg_sc`` command to segment the spinal cord from the anatomical image. The segmented spinal cord is a requirement for the vertebral/disc labeling stage that comes after. It is also a requirement for registration to the template (because some steps of the registration involve the segmentation) and for computing cord morphometrics, such as CSA.

Command: ``sct_deepseg_sc``
===========================

.. code:: sh

   sct_deepseg_sc -i t2.nii.gz -c t2 -qc ~/qc_singleSubj

   # Input arguments:
   #   - i: Input image
   #   - c: Contrast of the input image
   #   - qc: Directory for Quality Control reporting. QC reports allow us to evaluate the segmentation slice-by-slice

   # Output files/folders:
   #   - t2_seg.nii.gz: 3D binary mask of the segmented spinal cord

.. figure:: https://raw.githubusercontent.com/spinalcordtoolbox/doc-figures/master/spinalcord_segmentation/t2_propseg_before_after.png
   :align: center
   :figwidth: 65%

   Input/output images for ``sct_deepseg_sc``.

.. _vert-labeling-section:

Step 2: Vertebral/disc labeling
*******************************

.. figure:: https://raw.githubusercontent.com/spinalcordtoolbox/doc-figures/master/registration_to_template/registration-pipeline-2.png
   :align: center
   :figwidth: 75%

   Steps performed by ``sct_label_vertebrae`` and ``sct_label_utils``.

Theory
======

.. figure:: https://raw.githubusercontent.com/spinalcordtoolbox/doc-figures/master/registration_to_template/instrumentation-missing-discs.png
   :align: right
   :figwidth: 25%

   ``sct_label_vertebrae`` is able to label vertebral levels despite missing discs due to instrumentation.

Next, the segmented spinal cord must be labeled to provide reference markers for matching the PAM50 template to subject's MRI.  The vertebral/disc labeling algorithm works as follows:

  #. The spinal cord is straightened to make it easier to process.
  #. Then, labeling is done using an automatic method that finds the C2-C3 disc, then finds neighbouring discs using a similarity measure with the PAM50 template at each specific level.

     - The C2-C3 disc is used as a starting point because it is a distinct disc that is easy to detect (compared to, say, the T7-T9 discs, which are indistinct compared to one another).
     - The labeling algorithm uses several priors from the template, including the probabilistic distance between adjacent discs and the size of the vertebral discs. These priors allow it to be robust enough to handle cases where instrumentation results in missing discs.

  #. Finally, the spinal cord and the labeled segmentation are both un-straightened.


Label files are produced for both vertebral levels and intervertebral discs, and either can be used for the later registration steps. For vertebral levels, the convention is to place labels as though the vertebrae were projected onto the spinal cord, centered in the middle of the vertebral level. For discs, the convention is to place labels on the posterior tip of the disc.

.. figure:: https://raw.githubusercontent.com/spinalcordtoolbox/doc-figures/master/registration_to_template/vertebral-labeling-conventions.png
   :align: center
   :figwidth: 25%

   Conventions for vertebral and disc labels.

Command: ``sct_label_vertebrae``
================================

.. code:: sh

   sct_label_vertebrae -i t2.nii.gz -s t2_seg.nii.gz -c t2 -qc ~/qc_singleSubj

   # Input arguments:
   #   - i: Input image
   #   - c: Contrast of the input image
   #   - qc: Directory for Quality Control reporting. QC reports allow us to evaluate the results slice-by-slice.

   # Output files/folders:
   #   - t2_seg_labeled.nii.gz: Image containing the labeled spinal cord. Each voxel of the segmented spinal cord is
   #                            labeled with a vertebral level as though the vertebrae were projected onto the spinal
   #                            cord. The convention for label values is C3-->3, C4-->4, etc.
   #   - t2_seg_labeled_discs.nii.gz: Image containing single-voxel intervertebral disc labels (without the segmented
   #                                  spinal cord). Each label is centered within the disc. The convention for label
   #                                  values is C2/C3-->3, C3/C4-->4, etc. This file also contains additional labels
   #                                  (such as the pontomedullary junction and groove), but these are not yet used.
   #   - straight_ref.nii.gz: The straightened input image produced by the intermediate straightening step. Can be
   #                          re-used by other SCT functions that need a straight reference space.
   #   - warp_curve2straight.nii.gz: The 4D warping field that defines the transform from the original curved
   #                                 anatomical image to the straightened image.
   #   - warp_straight2curve.nii.gz: The 4D warping field that defines the inverse transform from the straightened
   #                                 anatomical image back to the original curved image.
   #   - straightening.cache: If sct_label_vertebrae is run another time, the presence of this file (plus
   #                          straight_ref.nii.gz and the two warping fields) will cause the straightening step to be
   #                          skipped, thus saving processing time.

.. note::

   If the labeling fails, you may also manually label the C2-C3 disc using ``sct_label_utils``, then re-run ``sct_label_vertebrae`` with this initialized image.

The most relevant output files are ``t2_seg_labeled.nii.gz`` and ``t2_seg_labeled_discs.nii.gz``. Either of them can be subsequently used for the template registration and/or for computing metrics along the cord. Of the two, we will focus on the ``t2_seg_labeled.nii.gz`` image for the remainder of this tutorial.

.. figure:: https://raw.githubusercontent.com/spinalcordtoolbox/doc-figures/master/registration_to_template/io-sct_label_vertebrae.png
   :align: center
   :figwidth: 65%

   Input/output images for ``sct_label_vertebrae``.

Command: ``sct_label_utils``
============================

Not all of the labels produced by ``sct_label_vertebrae`` are necessary for registration. To discard the extra vertebral levels, we use ``sct_label_utils`` to create a new label image containing only 2 of the labels. These points are used to match the levels of the subject to the levels of the template, and correspond to the top and bottom vertebrae we wish to use for image registration.

.. code:: sh

   sct_label_utils -i t2_seg_labeled.nii.gz -vert-body 3,9 -o t2_labels_vert.nii.gz

   # Input arguments:
   #   - i: Input image containing a spinal cord labeled with vertebral levels
   #   - vert-body: The vertebral levels to use when creating new point labels
   #   - o: Output filename

   # Output files/folders:
   #   - t2_labels_vert.nii.gz: Image containing the 2 single-voxel vertebral labels

.. figure:: https://raw.githubusercontent.com/spinalcordtoolbox/doc-figures/master/registration_to_template/io-sct_label_utils.png
   :align: center
   :figwidth: 65%

   Input/output images for ``sct_label_utils``.

.. note::

   As an alternative to automatic labeling, you may choose to label the spinal cord manually. ``sct_label_utils`` provides a ``-create-viewer`` argument which lets you select labels using a GUI coordinate picker. More information can be found in the usage description, using ``sct_label_utils -h``.

   If you provide more than 2 labels, there will be a non-linear transformation along z, which implies that everything above the top label and below the bottom label will be lost in the transformation. Therefore, if you are interested in regions outside of the specified labels, only use one or two labels, but no more.

.. _registration-section:

Step 3: Registering the anatomical image to the PAM50 template
**************************************************************

.. figure:: https://raw.githubusercontent.com/spinalcordtoolbox/doc-figures/master/registration_to_template/registration-pipeline-3.png
   :align: center
   :figwidth: 75%

   Steps performed by ``sct_register_to_template``

Theory
======

Now that we have the labeled spinal cord, we can register the anatomical image to the template.

.. figure:: https://raw.githubusercontent.com/spinalcordtoolbox/doc-figures/master/registration_to_template/thin-plate-straightening.png
   :align: right
   :figwidth: 30%

   Spinal cord straighting using thin-plate spline interpolation.

Internally, the ``sct_register_to_template`` command begins with a initial straightening step.  The straightening works by finding, for each point along the spinal cord, the mathematical transformation to go from a curved centerline to a straight centerline. A major advantage of the implemented straightening algorithm, is that instead of doing a slice-wise translation (which does not account for the through-plane deformation), the algorithm computes the orthogonal plane at each point along the centerline, then constructs a straight space in the output using thin-plate spline interpolation. This allows the inner geometry of the cord to be preserved. Another advantage is that it outputs a forward and a backward warping field (ITK-compatible), which could be concatenated with subsequent transformations, as will be seen later.

Once straightened, the next step involves an affine transformation to match the vertebral levels of the subject to that of the template using. This step focuses only on the coordinates of the labels, and does not consider the shape of the spinal cord (which is handled by the next step). Together, the straightening and level matching comprise "Step 0" of ``sct_register_to_template``.

After this, a multi-step nonrigid deformation is estimated to match the subject’s cord shape to the template. The default configuration starts with a step to handle large deformations ("Step 1"). This is followed by a step for fine adjustments ("Step 2").

.. note::

   The default settings should work for most cases. However, SCT provides a variety of algorithms with pros and cons depending on your data. You might want to play with the parameters of these steps to optimize registration for your particular contrast, resolution, and spinal cord geometry. The available settings are explored further in the :ref:`customizing-registration-section` section.

Command: ``sct_register_to_template``
=====================================

.. code:: sh

   sct_register_to_template -i t2.nii.gz -s t2_seg.nii.gz -l t2_labels_vert.nii.gz -c t2 -qc ~/qc_singleSubj

   # Input arguments:
   #   - i: Input image
   #   - s: Segmented spinal cord corresponding to the input image
   #   - l: One or two labels located at the center of the spinal cord, on the mid-vertebral slice
   #   - c: Contrast of the image. Specifying this determines which image from the template will be used.
   #     (e.g. t2 --> PAM50_t2.nii.gz)
   #   - qc: Directory for Quality Control reporting. QC reports allow us to evaluate the results slice-by-slice.

   # Output files/folders:
   #   - anat2template.nii.gz: The anatomical subject image (in this case, t2.nii.gz) warped to the template space.
   #   - template2anat.nii.gz: The template image (in this case, PAM50_t2.nii.gz) warped to the anatomical subject
   #                           space.
   #   - warp_anat2template.nii.gz: The 4D warping field that defines the transform from the anatomical image to the
   #                                template image.
   #   - warp_template2anat.nii.gz: The 4D warping field that defines the inverse transform from the template image to
   #                                the anatomical image.

The most relevant of the output files is ``warp_template2anat.nii.gz``, which will be used to transform the unbiased PAM50 template into the subject space (i.e. to match the ``t2.nii.gz`` anatomical image).

.. figure:: https://raw.githubusercontent.com/spinalcordtoolbox/doc-figures/master/registration_to_template/io-sct_register_to_template.png
   :align: center
   :figwidth: 65%

   Input/output images for ``sct_register_to_template``.

.. _transforming-template-section:

Step 4: Transforming template objects into the subject space
************************************************************

.. figure:: https://raw.githubusercontent.com/spinalcordtoolbox/doc-figures/master/registration_to_template/registration-pipeline-4.png
   :align: center
   :figwidth: 75%

   Steps performed by ``sct_warp_template``.

Theory
======

Once the transformations are estimated, we can apply the resulting warping field to the template to bring it into to the subject’s native space.

Command
=======

.. code:: sh

   sct_warp_template -d t2.nii.gz -w warp_template2anat.nii.gz -a 0 -qc ~/qc_singleSubj

   # Input arguments:
   #   - d: Destination image the template will be warped to.
   #   - w: Warping field (template space to anatomical space).
   #   - a: Whether or not to also warp the white matter atlas.
   #   - qc: Directory for Quality Control reporting. QC reports allow us to evaluate the results slice-by-slice.

   # Output:
   #   - label/template/: This directory contains the entirety of the PAM50 template, transformed into the subject
   #                      space (i.e. the t2.nii.gz anatomical image).

The ``label/template`` directory contains 15 template objects. (The full list can be found on the :ref:`pam50` page.) The most relevant of these 15 files for this tutorial is ``PAM50_levels.nii.gz``, which will be used to compute the the cross-sectional area (CSA) aggregated across vertebral levels.

.. figure:: https://raw.githubusercontent.com/spinalcordtoolbox/doc-figures/master/registration_to_template/io-sct_warp_template.png
   :align: center
   :figwidth: 65%

   Input/output images for ``sct_warp_template``.

.. _compute-metrics-section:

Step 5: Computing metrics (CSA and shape analysis)
**************************************************

Once the PAM50 template has been registered to the subject’s space, we can use it to do some quantitative analysis. This section demonstrates how to compute the cross-sectional area (CSA) of the spinal cord using ``sct_process_segmentation`` command.

By default, sct_process_segmentation will output a file called csa.csv, which contains CSA results (mean and STD) as well as the angles between the cord centerline and the normal to the axial plane. Angle_AP corresponds to the angle about the AP axis, while angle_RL corresponds to the angle about the RL axis. These angles are used to correct the CSA, therefore if you obtain inconsistent CSA values, it it a good habit to verify the value of these angles.

.. figure:: https://raw.githubusercontent.com/spinalcordtoolbox/doc-figures/master/registration_to_template/csa-angles.png
   :align: center
   :figwidth: 50%

   Visualization of CSA, as well as the angles (AP, RL) used to compute the CSA.

Averaging CSA across vertebral levels
=====================================

First, we  we compute the cord cross-sectional area (CSA) and average it between C3 and C4 vertebral levels. To specify these vertebral levels, we use the ``-vert`` argument.

.. code:: sh

   sct_process_segmentation -i t2_seg.nii.gz -vert 3:4 -o csa_c3c4.csv

This command generates a csv file named ``csa_c3c4.csv``, which is partially replicated in the table below.

.. csv-table:: CSA values computed for C3 and C4 vertebral levels (Averaged)
   :file: csa_c3c4.csv
   :header-rows: 1

.. note::

   The ``-vert`` flag used here relies on the vertebral labels defined by the ``-vertfile`` argument. The default value for ``-vertfile`` is ``./label/template/PAM50_levels.nii.gz``, so it is assumed that you have generated this file using the previous ``sct_warp_template`` command. However, you may specify a different vertebral label file by including the ``-vertfile`` argument.

   .. code:: sh

      sct_process_segmentation -i t2_seg.nii.gz -vert 3:4 -vertfile t2_seg_labeled.nii.gz -o csa_c3c4.csv

Computing CSA on a per-level basis
==================================

Next, we will compute CSA for each individual vertebral level (rather than averaging) by using the ``-perlevel`` argument.

.. code:: sh

   sct_process_segmentation -i t2_seg.nii.gz -vert 3:4 -perlevel 1 -o csa_perlevel.csv

This command generates a csv file named ``csa_perlevel.csv``, which is partially replicated in the table below.

.. csv-table:: CSA values computed for C3 and C4 vertebral levels
   :file: csa_perlevel.csv
   :header-rows: 1

Computing CSA on a per-slice basis
==================================

Finally, to compute CSA for individual slices, set the ``-perslice`` argument to 1, combined with the ``-z`` argument to specify slice numbers (or a range of slices).

.. code:: sh

   sct_process_segmentation -i t2_seg.nii.gz -z 30:35 -perslice 1 -o csa_perslice.csv

This command generates a csv file named ``csa_perslice.csv``, which is partially replicated in the table below.

.. csv-table:: CSA values across slices 30 to 35
   :file: csa_perslice.csv
   :header-rows: 1

Shape analysis
==============

The csv files generated by ``sct_process_segmentation`` also include metrics to analyse the shape of the spinal cord in the axial plane, such as ellipticity, antero-posterior and right-left dimensions. These are of particular interest for studying cord compression. See [Martin et al. BMJ Open 2018] for an example application in degenerative cervical myelopathy.

.. figure:: https://raw.githubusercontent.com/spinalcordtoolbox/doc-figures/master/registration_to_template/sct_process_segmentation-shape-metrics.png
   :align: center
   :figwidth: 75%

   Additional shape metrics computed by ``sct_process_segmentation``.